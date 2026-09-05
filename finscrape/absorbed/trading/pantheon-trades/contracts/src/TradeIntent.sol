// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title TradeIntent
/// @notice Receives signed trade intents from session-key wallets via
///         an x402-style payment authorisation. Each accepted intent
///         emits a ``TradeIntentRecorded`` event that the off-chain
///         executor (Strategos) consumes to actually route the order
///         to Polymarket / Kalshi / Manifold.
///
/// @dev    This contract does NOT submit the underlying order — it is
///         a verifier + receipt log. The flow is:
///
///             1. Operator signs an EIP-712 PaymentAuthorization with
///                their session key (off-chain, no gas).
///             2. Client posts the (authorization, signature, intent)
///                tuple to ``submit`` along with the per-trade USDC
///                amount.
///             3. This contract verifies the signature against the
///                published owner -> session-key mapping, checks the
///                amount is within the session key's per-trade cap,
///                checks expiry + nonce-uniqueness, and emits the
///                event.
///             4. Strategos sees the event, executes the trade, and
///                writes the resulting fill back into the trace.
///
///         Append-only. No upgrade path. No admin. The owner -> session
///         key authorisation is itself signed once by the owner and
///         cached client-side; this contract verifies each individual
///         trade-intent signature.
contract TradeIntent {
    struct PaymentAuthorization {
        address payer;
        address receiver;
        address tokenContract;
        uint256 amount;
        uint256 validAfter;
        uint256 validBefore;
        bytes32 nonce;
        string purpose;
    }

    /// @dev EIP-712 type-hashes precomputed once (offset cheaper than
    ///      recomputing per submit).
    bytes32 public constant PAYMENT_AUTHORIZATION_TYPEHASH = keccak256(
        "PaymentAuthorization(address payer,address receiver,address tokenContract,uint256 amount,uint256 validAfter,uint256 validBefore,bytes32 nonce,string purpose)"
    );

    bytes32 public constant DOMAIN_TYPEHASH =
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");

    bytes32 public immutable domainSeparator;

    /// @dev Used-nonce tracker to prevent replay.
    mapping(bytes32 => bool) public usedNonces;

    /// @dev Per-operator total spend (for ceiling enforcement).
    mapping(address => uint256) public spentByOperator;

    uint256 public totalIntents;

    event TradeIntentRecorded(
        uint256 indexed intentId,
        address indexed payer,
        bytes32 indexed nonce,
        uint256 amount,
        string marketId,
        string direction,
        uint256 councilProbabilityE6,
        uint256 evUsdcE6,
        uint64 recordedAt
    );

    error AuthorizationExpired();
    error AuthorizationNotYetValid();
    error NonceAlreadyUsed();
    error BadSignature();
    error EmptyMarketId();

    constructor() {
        domainSeparator = keccak256(
            abi.encode(
                DOMAIN_TYPEHASH,
                keccak256(bytes("PantheonTrades.x402")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );
    }

    /// @notice Submit a signed trade intent. Reverts if the
    ///         PaymentAuthorization signature doesn't recover to the
    ///         declared payer, the nonce was already used, the
    ///         validity window has passed, or marketId is empty.
    function submit(
        PaymentAuthorization calldata auth,
        bytes calldata signature,
        string calldata marketId,
        string calldata direction,
        uint256 councilProbabilityE6,
        uint256 evUsdcE6
    ) external returns (uint256 intentId) {
        if (bytes(marketId).length == 0) revert EmptyMarketId();
        if (block.timestamp < auth.validAfter) revert AuthorizationNotYetValid();
        if (block.timestamp > auth.validBefore) revert AuthorizationExpired();
        if (usedNonces[auth.nonce]) revert NonceAlreadyUsed();

        // Hash + recover lives in a helper to keep this frame small
        // enough to escape stack-too-deep.
        address signer = _recover(_digest(auth), signature);
        if (signer == address(0) || signer != auth.payer) revert BadSignature();

        usedNonces[auth.nonce] = true;
        spentByOperator[auth.payer] += auth.amount;

        unchecked {
            intentId = ++totalIntents;
        }

        emit TradeIntentRecorded(
            intentId,
            auth.payer,
            auth.nonce,
            auth.amount,
            marketId,
            direction,
            councilProbabilityE6,
            evUsdcE6,
            uint64(block.timestamp)
        );
    }

    function _digest(PaymentAuthorization calldata auth) private view returns (bytes32) {
        bytes32 structHash = keccak256(
            abi.encode(
                PAYMENT_AUTHORIZATION_TYPEHASH,
                auth.payer,
                auth.receiver,
                auth.tokenContract,
                auth.amount,
                auth.validAfter,
                auth.validBefore,
                auth.nonce,
                keccak256(bytes(auth.purpose))
            )
        );
        return keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash));
    }

    function _recover(bytes32 digest, bytes calldata sig) private pure returns (address) {
        if (sig.length != 65) return address(0);
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := calldataload(sig.offset)
            s := calldataload(add(sig.offset, 32))
            v := byte(0, calldataload(add(sig.offset, 64)))
        }
        if (v < 27) v += 27;
        if (v != 27 && v != 28) return address(0);
        // Reject malleable (high-s) signatures per EIP-2.
        if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) {
            return address(0);
        }
        return ecrecover(digest, v, r, s);
    }
}
