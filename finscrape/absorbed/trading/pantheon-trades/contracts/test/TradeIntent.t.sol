// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";

import {TradeIntent} from "../src/TradeIntent.sol";

contract TradeIntentTest is Test {
    TradeIntent internal ti;
    uint256 internal payerPrivateKey;
    address internal payerAddress;

    function setUp() public {
        ti = new TradeIntent();
        payerPrivateKey = 0xA11CE;
        payerAddress = vm.addr(payerPrivateKey);
    }

    function _sign(TradeIntent.PaymentAuthorization memory auth)
        internal
        view
        returns (bytes memory sig)
    {
        bytes32 structHash = keccak256(
            abi.encode(
                ti.PAYMENT_AUTHORIZATION_TYPEHASH(),
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
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", ti.domainSeparator(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(payerPrivateKey, digest);
        sig = abi.encodePacked(r, s, v);
    }

    function _auth() internal view returns (TradeIntent.PaymentAuthorization memory) {
        return TradeIntent.PaymentAuthorization({
            payer: payerAddress,
            receiver: address(ti),
            tokenContract: address(0xCAFE),
            amount: 5_000_000, // 5 USDC (6-dp)
            validAfter: block.timestamp - 1,
            validBefore: block.timestamp + 300,
            nonce: keccak256("nonce-1"),
            purpose: "council:approve"
        });
    }

    function test_SubmitWithValidSignatureEmitsEvent() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        bytes memory sig = _sign(auth);
        vm.recordLogs();
        uint256 id = ti.submit(auth, sig, "market-1", "YES", 590000, 1_500_000);
        assertEq(id, 1);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 1);
    }

    function test_NonceCannotBeReused() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        bytes memory sig = _sign(auth);
        ti.submit(auth, sig, "m", "YES", 5, 1);
        vm.expectRevert(TradeIntent.NonceAlreadyUsed.selector);
        ti.submit(auth, sig, "m", "YES", 5, 1);
    }

    function test_RejectsExpiredAuthorization() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        auth.validBefore = block.timestamp - 1;
        bytes memory sig = _sign(auth);
        vm.expectRevert(TradeIntent.AuthorizationExpired.selector);
        ti.submit(auth, sig, "m", "YES", 5, 1);
    }

    function test_RejectsNotYetValidAuthorization() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        auth.validAfter = block.timestamp + 600;
        auth.validBefore = block.timestamp + 1200;
        bytes memory sig = _sign(auth);
        vm.expectRevert(TradeIntent.AuthorizationNotYetValid.selector);
        ti.submit(auth, sig, "m", "YES", 5, 1);
    }

    function test_RejectsBadSignature() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        // Signature from a different key.
        uint256 stranger = 0xB0B;
        bytes32 structHash = keccak256(
            abi.encode(
                ti.PAYMENT_AUTHORIZATION_TYPEHASH(),
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
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", ti.domainSeparator(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(stranger, digest);
        bytes memory sig = abi.encodePacked(r, s, v);
        vm.expectRevert(TradeIntent.BadSignature.selector);
        ti.submit(auth, sig, "m", "YES", 5, 1);
    }

    function test_RejectsEmptyMarketId() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        bytes memory sig = _sign(auth);
        vm.expectRevert(TradeIntent.EmptyMarketId.selector);
        ti.submit(auth, sig, "", "YES", 5, 1);
    }

    function test_TracksTotalIntentsMonotonically() public {
        for (uint256 i = 1; i <= 3; i++) {
            TradeIntent.PaymentAuthorization memory auth = _auth();
            auth.nonce = keccak256(abi.encodePacked("nonce", i));
            bytes memory sig = _sign(auth);
            uint256 id = ti.submit(auth, sig, "m", "YES", 5, 1);
            assertEq(id, i);
        }
        assertEq(ti.totalIntents(), 3);
    }

    function test_TracksSpendByOperator() public {
        TradeIntent.PaymentAuthorization memory auth = _auth();
        auth.amount = 5_000_000;
        bytes memory sig = _sign(auth);
        ti.submit(auth, sig, "m1", "YES", 5, 1);

        auth.amount = 3_000_000;
        auth.nonce = keccak256("nonce-2");
        sig = _sign(auth);
        ti.submit(auth, sig, "m2", "NO", 4, 1);

        assertEq(ti.spentByOperator(payerAddress), 8_000_000);
    }
}
