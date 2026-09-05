// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";

import {TradeIntent} from "../src/TradeIntent.sol";

/// @title DeployTradeIntent
/// @notice Deploys the x402 trade-intent receiver on Arc Testnet. No
///         constructor args. After deploy, set
///         ``NEXT_PUBLIC_TRADE_INTENT_ADDRESS`` in apps/web/.env so the
///         /trade UI signs against the right verifyingContract.
contract DeployTradeIntent is Script {
    function run() external returns (TradeIntent ti) {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);
        console2.log("Deployer:", deployer);

        vm.startBroadcast(pk);
        ti = new TradeIntent();
        vm.stopBroadcast();

        console2.log("TradeIntent:", address(ti));
    }
}
