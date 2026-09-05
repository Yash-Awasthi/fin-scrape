// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ZeusMultisig
/// @notice Minimal M-of-N multisig wrapping calls. Confirmation tally tracked
///         per (target, data, value) tuple; once threshold met the call
///         executes once.
contract ZeusMultisig {
    address[] public signers;
    uint256 public immutable threshold;

    mapping(bytes32 => uint256) public confirmations;
    mapping(bytes32 => mapping(address => bool)) public confirmedBy;
    mapping(bytes32 => bool) public executed;

    event Confirmed(bytes32 indexed callId, address indexed signer, uint256 confirmations);
    event Executed(bytes32 indexed callId, address target, uint256 value);

    error NotSigner();
    error AlreadyConfirmed();
    error AlreadyExecuted();
    error InsufficientConfirmations();

    constructor(
        address[] memory _signers,
        uint256 _threshold
    ) {
        require(_threshold > 0 && _threshold <= _signers.length, "bad threshold");
        signers = _signers;
        threshold = _threshold;
    }

    function isSigner(
        address who
    ) public view returns (bool) {
        for (uint256 i = 0; i < signers.length; ++i) {
            if (signers[i] == who) return true;
        }
        return false;
    }

    function confirm(
        address target,
        uint256 value,
        bytes calldata data
    ) external {
        if (!isSigner(msg.sender)) revert NotSigner();
        bytes32 callId = keccak256(abi.encode(target, value, data));
        if (executed[callId]) revert AlreadyExecuted();
        if (confirmedBy[callId][msg.sender]) revert AlreadyConfirmed();
        confirmedBy[callId][msg.sender] = true;
        confirmations[callId] += 1;
        emit Confirmed(callId, msg.sender, confirmations[callId]);
    }

    // This contract is a multisig — the entire point is that the
    // approved set of signers can call an arbitrary target after
    // reaching `threshold` confirmations. Slither's arbitrary-send-eth
    // detector flags `target.call{value: value}(data)` as dangerous
    // in a generic context, but here the destination is gated by the
    // `confirmations[callId] >= threshold` check inside the function.
    // That gate IS the security boundary. The directive immediately
    // above the `target.call` line below suppresses the false positive
    // — slither-disable-next-line requires the directive on the
    // line directly preceding the offending statement (no other
    // comments allowed between them), so the rationale lives in this
    // function-level NatSpec instead.
    // slither-disable-start arbitrary-send-eth
    function execute(
        address target,
        uint256 value,
        bytes calldata data
    ) external {
        bytes32 callId = keccak256(abi.encode(target, value, data));
        if (executed[callId]) revert AlreadyExecuted();
        if (confirmations[callId] < threshold) revert InsufficientConfirmations();
        executed[callId] = true;
        (bool ok,) = target.call{ value: value }(data);
        require(ok, "call failed");
        emit Executed(callId, target, value);
    }
    // slither-disable-end arbitrary-send-eth

    receive() external payable { }
}
