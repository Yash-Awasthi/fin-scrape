/**
 * Signal Content Library
 *
 * Natural-language briefings for families based on indicator patterns.
 * Written conversationally, like someone explaining the situation over coffee.
 */

import { ActionItem } from '../components/dashboard/LeadCard';

export interface SignalContent {
  category: string;
  headline: string;
  whatsHappening: string;         // The situation (conversational)
  whyItMatters: string;           // Impact on your family
  whatToDo: string;               // Quick 1-sentence summary
  actions: ActionItem[];          // Detailed expandable actions
  indicatorIds: string[];
  urgency: 'today' | 'week' | 'knowing';
}

// ═══════════════════════════════════════════════════════════════════════════
// INFRASTRUCTURE
// ═══════════════════════════════════════════════════════════════════════════
export const INFRASTRUCTURE_SIGNAL: SignalContent = {
  category: 'INFRASTRUCTURE STRESS',
  headline: 'Power grid showing strain as cyber threats increase',
  whatsHappening: "Here's what I'm seeing: the power grid is stressed. Outage reports are up 23% this quarter, mostly in Texas and the Northeast. Meanwhile, hackers are actively targeting power plant systems—CISA flagged 4 new industrial vulnerabilities this month. When these things happen together, the risk of longer blackouts goes up.",
  whyItMatters: "If the power goes out for more than a day, your freezer food starts to spoil. Your generator can keep the basics running, but only for about 48 hours on a full tank. This is a good week to make sure everything's topped off and ready.",
  whatToDo: "Test your backup power and top off fuel.",
  actions: [
    { id: 'infra-1', text: 'Fire up the generator to make sure it starts, check the fuel', estimateMinutes: 15 },
    { id: 'infra-2', text: 'Plug in all the battery packs and power stations', estimateMinutes: 5 },
    { id: 'infra-3', text: 'Download offline maps in case cell service gets spotty', estimateMinutes: 10 },
  ],
  indicatorIds: ['cyber_01_cisa_kev', 'grid_01_pjm_outages'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// OIL & ENERGY
// ═══════════════════════════════════════════════════════════════════════════
export const OIL_SECURITY_SIGNAL: SignalContent = {
  category: 'ENERGY SUPPLY',
  headline: 'Oil reserves are getting low—heating costs likely to jump',
  whatsHappening: "Here's the situation: the Strategic Petroleum Reserve is down to 350 million barrels, which is getting close to levels that have historically spooked markets. Global oil stocks are running about 8% below normal. Last time things looked like this, heating oil prices jumped 40% in a single quarter. Winter is about three months out.",
  whyItMatters: "Your oil company tends to raise prices fast when reserves drop like this, and delivery schedules get less reliable. If you usually wait until fall to fill the tank, this year it might be worth calling early—before everyone else has the same idea.",
  whatToDo: "Schedule an early heating oil fill and check your tank level.",
  actions: [
    { id: 'oil-1', text: 'Call your oil company and schedule an early fill', estimateMinutes: 10 },
    { id: 'oil-2', text: "Check the tank gauge and note where you're at", estimateMinutes: 5 },
    { id: 'oil-3', text: 'Think about backup heating—space heaters, propane, whatever makes sense', estimateMinutes: 20 },
  ],
  indicatorIds: ['spr_01_level', 'oil_03_jodi_inventory', 'oil_02_mbridge_settlements'],
  urgency: 'today',
};

// ═══════════════════════════════════════════════════════════════════════════
// JOBS & LABOR
// ═══════════════════════════════════════════════════════════════════════════
export const LABOR_SIGNAL: SignalContent = {
  category: 'JOBS & LABOR',
  headline: 'Layoffs picking up, especially in tech',
  whatsHappening: "Here's what I'm tracking: tech and logistics companies have ramped up layoffs—announcements are up 45% from last month. Strike activity is at a five-year high. Jobless claims ticked up to 245,000 last week, which isn't crisis territory, but the trend is heading the wrong direction. And pharmacy shortages are making some prescriptions harder to fill.",
  whyItMatters: "When layoffs spike in your field, job searches tend to take longer—often 5+ months instead of 3. Worth thinking about whether your emergency fund would cover that. Also a good time to make sure you've got extra refills on any medications you take regularly.",
  whatToDo: "Update your resume and stock up on essential prescriptions.",
  actions: [
    { id: 'labor-1', text: 'Dust off the resume and update LinkedIn', estimateMinutes: 45 },
    { id: 'labor-2', text: 'Ask your pharmacy for 90-day refills on essential meds', estimateMinutes: 15 },
    { id: 'labor-3', text: 'Do a quick check on your monthly expenses vs. savings', estimateMinutes: 20 },
  ],
  indicatorIds: ['job_01_strike_days', 'labor_ai_01_layoffs', 'job_01_jobless_claims', 'supply_pharmacy_shortage'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// ECONOMY & MARKETS
// ═══════════════════════════════════════════════════════════════════════════
export const FINANCIAL_SIGNAL: SignalContent = {
  category: 'ECONOMY',
  headline: 'Bond market getting shaky, groceries still climbing',
  whatsHappening: "Here's what happened: yesterday's Treasury auction didn't go well—the weakest demand since late 2023. That matters because it affects interest rates on everything from mortgages to car loans. Meanwhile, grocery prices are still running hot: eggs up 22%, beef up 15%. The stock market has been swinging 2%+ on 8 of the last 20 trading days.",
  whyItMatters: "If you have an adjustable-rate mortgage, this could mean your payment goes up at the next reset. And if you've noticed your grocery bill creeping higher, you're not imagining it. Might be worth shifting some investments to cash until things settle down.",
  whatToDo: "Review your mortgage terms and build up cash reserves.",
  actions: [
    { id: 'fin-1', text: 'Check your mortgage terms—is it adjustable? When does it reset?', estimateMinutes: 15 },
    { id: 'fin-2', text: 'Consider moving a few months of expenses to savings', estimateMinutes: 15 },
    { id: 'fin-3', text: 'Stock up on pantry staples when they go on sale', estimateMinutes: 10 },
  ],
  indicatorIds: ['econ_01_treasury_tail', 'econ_02_grocery_cpi', 'market_01_intraday_swing'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// TRAVEL
// ═══════════════════════════════════════════════════════════════════════════
export const TRAVEL_SIGNAL: SignalContent = {
  category: 'TRAVEL',
  headline: 'Passport renewals taking longer, more travel advisories',
  whatsHappening: "Here's what's going on: passport processing has slipped to 10-12 weeks, up from the usual 6-8. The State Department has issued or upgraded travel advisories for 7 countries this month. Border wait times are up 23%, and there have been 4 FAA ground stops due to system issues. International travel is just getting more complicated.",
  whyItMatters: "Most countries require your passport to be valid for at least 6 months after your trip. If anyone in the family has a passport expiring in the next year, now's the time to renew—before the summer rush makes wait times even worse.",
  whatToDo: "Check passport expiration dates and submit renewals now.",
  actions: [
    { id: 'travel-1', text: "Pull out everyone's passports and check the dates", estimateMinutes: 5 },
    { id: 'travel-2', text: 'Submit renewals now for anything expiring within 12 months', estimateMinutes: 45 },
    { id: 'travel-3', text: 'Make sure travel insurance covers trip interruption', estimateMinutes: 15 },
  ],
  indicatorIds: ['state_dept_travel', 'cbp_wait_times', 'faa_ground_stops'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// GLOBAL SITUATION
// ═══════════════════════════════════════════════════════════════════════════
export const GLOBAL_CONFLICT_SIGNAL: SignalContent = {
  category: 'GLOBAL SITUATION',
  headline: 'Tensions rising in Asia and the Middle East',
  whatsHappening: "Here's the bigger picture: Chinese military activity near Taiwan has been nearly daily—28 out of 30 days this past month. Three carrier groups are operating in the Western Pacific. NATO has raised its readiness levels, and shipping insurance through the Strait of Hormuz has doubled. None of this means war is imminent, but the world is more on edge than usual.",
  whyItMatters: "If something does happen in Taiwan, chip production stops—and that affects everything from your laptop to your car. Might be worth making sure your essential electronics are in good shape, and thinking about whether your investments are too concentrated in companies that depend on Asian manufacturing.",
  whatToDo: "Review your investment exposure and ensure essential electronics work.",
  actions: [
    { id: 'conflict-1', text: 'Take a look at what your investments are exposed to', estimateMinutes: 30 },
    { id: 'conflict-2', text: 'Make sure your main devices are working well', estimateMinutes: 10 },
    { id: 'conflict-3', text: "Consider grabbing a spare router while they're available", estimateMinutes: 15 },
  ],
  indicatorIds: ['taiwan_pla_activity', 'nato_high_readiness', 'hormuz_war_risk', 'global_conflict_intensity'],
  urgency: 'knowing',
};

// ═══════════════════════════════════════════════════════════════════════════
// DOMESTIC POLICY
// ═══════════════════════════════════════════════════════════════════════════
export const DOMESTIC_CONTROL_SIGNAL: SignalContent = {
  category: 'DOMESTIC POLICY',
  headline: 'Immigration enforcement and processing backlogs increasing',
  whatsHappening: "Here's what I'm watching: ICE detention facilities are at 94% capacity—the highest since 2019. DHS has issued new enforcement directives this quarter, and National Guard deployments to cities are up 40%. Congress is also considering several bills that would expand surveillance authority. Processing times for visa renewals have gotten longer.",
  whyItMatters: "If anyone in your household is on a visa or has pending immigration paperwork, now's a good time to double-check that everything is current and to confirm timelines with an attorney. Delays and backlogs are real right now.",
  whatToDo: "Verify all immigration documents are current and accessible.",
  actions: [
    { id: 'domestic-1', text: 'Make sure all immigration documents are current and easy to find', estimateMinutes: 15 },
    { id: 'domestic-2', text: 'Check in with your immigration attorney about timelines', estimateMinutes: 20 },
    { id: 'domestic-3', text: "Review your family's emergency communication plan", estimateMinutes: 15 },
  ],
  indicatorIds: ['ice_detention_surge', 'dhs_removal_expansion', 'national_guard_metros', 'hill_control_legislation'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH
// ═══════════════════════════════════════════════════════════════════════════
export const HEALTH_BIOSECURITY_SIGNAL: SignalContent = {
  category: 'HEALTH',
  headline: 'Medication shortages and disease alerts worth watching',
  whatsHappening: "Here's what I'm seeing on the health front: the FDA's drug shortage list has grown to 137 medications, including some common antibiotics and diabetes drugs. Internationally, WHO has flagged disease outbreaks in 5 countries with confirmed human-to-human transmission. Hospital capacity in 12 states is running above 85%, which doesn't leave much room for a surge.",
  whyItMatters: "If anyone in your family takes daily medication, it's worth checking if it's on the shortage list and asking for a 90-day supply. And while there's no immediate outbreak concern here, it doesn't hurt to make sure your first aid supplies are stocked.",
  whatToDo: "Request 90-day prescription refills and restock first aid supplies.",
  actions: [
    { id: 'health-1', text: 'Ask your pharmacy for 90-day refills on critical prescriptions', estimateMinutes: 15 },
    { id: 'health-2', text: 'Restock the first aid kit and basic OTC meds', estimateMinutes: 25 },
    { id: 'health-3', text: 'Make sure your insurance covers telehealth visits', estimateMinutes: 10 },
  ],
  indicatorIds: ['bio_01_h2h_countries', 'supply_pharmacy_shortage'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// BANKING & HOUSING
// ═══════════════════════════════════════════════════════════════════════════
export const BANKING_STRESS_SIGNAL: SignalContent = {
  category: 'BANKING & HOUSING',
  headline: 'Banks under pressure, mortgage stress rising',
  whatsHappening: "Here's what I'm watching in the financial system: bank failures are above historical norms, and more regional banks are tapping the Fed's emergency lending window. Mortgage delinquencies have ticked up 0.4% this quarter, and rate shock is hitting homeowners with adjustable mortgages. The luxury real estate market—often an early warning signal—has cooled significantly.",
  whyItMatters: "If you have savings spread across multiple banks, now's a good time to check that each account is under the FDIC limit. If your mortgage is adjustable, review when the next rate reset happens. Even if you're not directly affected, credit conditions tend to tighten when banks are stressed.",
  whatToDo: "Verify FDIC coverage and review your mortgage terms.",
  actions: [
    { id: 'bank-1', text: 'Check that each bank account is under $250K FDIC limit', estimateMinutes: 10 },
    { id: 'bank-2', text: 'Review your mortgage terms—fixed vs. adjustable, reset dates', estimateMinutes: 15 },
    { id: 'bank-3', text: 'Consider moving excess savings to Treasury bills or money market', estimateMinutes: 20 },
  ],
  indicatorIds: ['bank_01_failures', 'bank_02_discount_window', 'bank_03_deposit_flow', 'housing_01_delinquency', 'housing_03_rate_shock'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// SUPPLY CHAIN
// ═══════════════════════════════════════════════════════════════════════════
export const SUPPLY_CHAIN_SIGNAL: SignalContent = {
  category: 'SUPPLY CHAIN',
  headline: 'Shipping delays and chip shortages affecting availability',
  whatsHappening: "Here's the supply chain picture: port congestion is above normal, with container ships waiting longer to unload. Freight costs have jumped as capacity tightens. The chip shortage hasn't fully resolved—lead times are still elevated for automotive and electronics components. If you're planning a major purchase, availability may be spotty.",
  whyItMatters: "This affects everything from car repairs to appliance deliveries. If you need a specific part or product, ordering now is better than waiting. Auto repairs that need specialty chips could face weeks of delay. Even everyday items might see sporadic stock-outs.",
  whatToDo: "Order essential items now and consider delaying major purchases.",
  actions: [
    { id: 'supply-1', text: 'Order any car parts or appliance components you might need soon', estimateMinutes: 20 },
    { id: 'supply-2', text: 'Stock up on items with complex supply chains (electronics, certain foods)', estimateMinutes: 30 },
    { id: 'supply-3', text: 'If planning a big purchase, check delivery timelines and inventory', estimateMinutes: 15 },
  ],
  indicatorIds: ['supply_01_port_congestion', 'supply_02_freight_index', 'supply_03_chip_lead_time'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// WATER INFRASTRUCTURE
// ═══════════════════════════════════════════════════════════════════════════
export const WATER_INFRASTRUCTURE_SIGNAL: SignalContent = {
  category: 'WATER',
  headline: 'Water supply showing early stress signs',
  whatsHappening: "Here's what's happening with water: reservoir levels in key regions are below seasonal averages, and there have been treatment facility alerts this month. Municipal water systems are aging, and when reservoirs drop, treatment plants work harder—which can lead to boil advisories or quality issues. This is more about being aware than panicking.",
  whyItMatters: "Water is one of those things you don't think about until there's a problem. Having a few days of backup water and a simple filter isn't paranoid—it's just practical. It also helps during any disruption, from a pipe break to a natural disaster.",
  whatToDo: "Check your water storage and consider a basic filtration option.",
  actions: [
    { id: 'water-1', text: 'Store at least 1 gallon per person per day for 3 days', estimateMinutes: 20 },
    { id: 'water-2', text: 'Get a quality water filter (Berkey, Sawyer, or similar)', estimateMinutes: 15 },
    { id: 'water-3', text: 'Know where your water shutoff valve is located', estimateMinutes: 5 },
  ],
  indicatorIds: ['water_01_reservoir_level', 'water_02_treatment_alerts'],
  urgency: 'knowing',
};

// ═══════════════════════════════════════════════════════════════════════════
// TELECOM & INTERNET
// ═══════════════════════════════════════════════════════════════════════════
export const TELECOM_SIGNAL: SignalContent = {
  category: 'COMMUNICATIONS',
  headline: 'Internet and cell networks showing vulnerabilities',
  whatsHappening: "Here's what I'm tracking on the communications front: BGP routing anomalies are elevated—that's the internet's addressing system, and problems there can cause widespread outages. Cell network issues have been reported in several markets. And there's been increased activity around undersea cables, which carry 95% of intercontinental data. None of this is immediate crisis, but it's worth noting.",
  whyItMatters: "If the internet or cell service goes down for a day or more, it affects everything from payments to navigation. Having offline backups of important information and an alternative communication plan with family becomes valuable insurance.",
  whatToDo: "Download offline resources and establish a family communication backup.",
  actions: [
    { id: 'telecom-1', text: 'Download offline maps for your area and common destinations', estimateMinutes: 10 },
    { id: 'telecom-2', text: 'Agree on a family meeting point if phones don\'t work', estimateMinutes: 5 },
    { id: 'telecom-3', text: 'Consider a battery-powered radio for emergency broadcasts', estimateMinutes: 15 },
    { id: 'telecom-4', text: 'Save important documents and contacts offline', estimateMinutes: 20 },
  ],
  indicatorIds: ['telecom_01_bgp_anomalies', 'telecom_02_cell_outages', 'telecom_03_undersea_cable'],
  urgency: 'knowing',
};

// ═══════════════════════════════════════════════════════════════════════════
// CIVIL LIBERTIES & GOVERNANCE
// ═══════════════════════════════════════════════════════════════════════════
export const CIVIL_LIBERTY_SIGNAL: SignalContent = {
  category: 'GOVERNANCE',
  headline: 'Policy shifts affecting privacy and civil liberties',
  whatsHappening: "Here's what's happening in the governance space: protest activity is elevated, which often signals broader social tensions. There's been new legislation around AI surveillance capabilities, and active court cases challenging various policies have increased. Federal regulations are being issued at an above-average pace. These are the kinds of shifts that can affect daily life in subtle ways.",
  whyItMatters: "Policy changes can affect travel, banking, and privacy over time. It's worth understanding where things are heading—not to be alarmed, but to make informed decisions about your digital footprint and documentation.",
  whatToDo: "Review your digital privacy settings and keep important documents current.",
  actions: [
    { id: 'liberty-1', text: 'Review privacy settings on social media and devices', estimateMinutes: 20 },
    { id: 'liberty-2', text: 'Ensure passports and ID documents are current', estimateMinutes: 10 },
    { id: 'liberty-3', text: 'Keep copies of important documents in a secure location', estimateMinutes: 15 },
  ],
  indicatorIds: ['civil_01_acled_protests', 'power_01_ai_surveillance', 'liberty_litigation_count', 'federal_regulations'],
  urgency: 'knowing',
};

// ═══════════════════════════════════════════════════════════════════════════
// AVIATION & TRANSPORT
// ═══════════════════════════════════════════════════════════════════════════
export const AVIATION_SIGNAL: SignalContent = {
  category: 'AVIATION',
  headline: 'Air travel disruptions more frequent than usual',
  whatsHappening: "Here's the air travel situation: FAA ground stops have been more frequent this month, often due to system issues or weather convergence. Flight delays are running above seasonal norms. Temporary flight restrictions have increased in certain regions. If you have travel planned, building in extra buffer time is wise.",
  whyItMatters: "Flight disruptions cascade—one delay affects connections, hotel bookings, and plans. If you have an important trip, consider direct flights when possible and have a backup plan for getting where you need to go.",
  whatToDo: "Build buffer time into travel plans and review cancellation policies.",
  actions: [
    { id: 'aviation-1', text: 'Check airline policies on rebooking and delays', estimateMinutes: 10 },
    { id: 'aviation-2', text: 'Book direct flights for critical trips when possible', estimateMinutes: 15 },
    { id: 'aviation-3', text: 'Download airline apps for real-time updates', estimateMinutes: 5 },
    { id: 'aviation-4', text: 'Have a ground transportation backup for critical destinations', estimateMinutes: 10 },
  ],
  indicatorIds: ['flight_01_ground_stops', 'flight_02_delay_pct', 'flight_03_tfr_count', 'travel_03_tsa_throughput'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// DISASTER & EMERGENCY SERVICES
// ═══════════════════════════════════════════════════════════════════════════
export const DISASTER_SIGNAL: SignalContent = {
  category: 'EMERGENCIES',
  headline: 'Emergency services stretched, disaster activity elevated',
  whatsHappening: "Here's the emergency services picture: FEMA has issued more disaster declarations this year than average—flooding, severe storms, and wildfires are all contributing. CDC has active health alerts in several regions. Grid emergency events have occurred in multiple states. This means emergency response resources are more stretched than usual.",
  whyItMatters: "When disaster response is stretched thin, self-sufficiency matters more. Having 72 hours of supplies means you're not competing for resources immediately after an event. It also gives first responders room to help those who really need it.",
  whatToDo: "Ensure your emergency kit is complete and know your local risks.",
  actions: [
    { id: 'disaster-1', text: 'Check that your 72-hour kit is stocked and current', estimateMinutes: 30 },
    { id: 'disaster-2', text: 'Review evacuation routes for your area', estimateMinutes: 15 },
    { id: 'disaster-3', text: 'Sign up for local emergency alerts (Notify, AlertMedia, etc.)', estimateMinutes: 10 },
    { id: 'disaster-4', text: 'Confirm insurance coverage is adequate and current', estimateMinutes: 20 },
  ],
  indicatorIds: ['fema_disaster_declarations', 'cdc_health_alerts', 'energy_03_grid_emergency', 'grid_01_pjm_outages'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// NATURAL GAS & HEATING
// ═══════════════════════════════════════════════════════════════════════════
export const NATURAL_GAS_SIGNAL: SignalContent = {
  category: 'HEATING',
  headline: 'Natural gas storage below normal heading into heating season',
  whatsHappening: "Here's the natural gas situation: storage levels are running below the 5-year average heading into the colder months. Last winter saw price spikes when cold snaps hit. Utility companies may pass higher costs through, and if storage stays low, heating bills could jump 20-30% compared to last year.",
  whyItMatters: "For homes heated by natural gas, this could mean noticeably higher utility bills. It's a good time to check your weatherization—sealing drafts and adding insulation can offset price increases. If you have backup heating options, make sure they're ready.",
  whatToDo: "Weatherize your home and budget for potentially higher heating costs.",
  actions: [
    { id: 'gas-1', text: 'Check windows and doors for drafts, add weatherstripping', estimateMinutes: 45 },
    { id: 'gas-2', text: 'Schedule furnace maintenance before the heating season', estimateMinutes: 10 },
    { id: 'gas-3', text: 'Budget 20-30% higher for heating bills this winter', estimateMinutes: 10 },
    { id: 'gas-4', text: 'Ensure backup heating (space heaters, fireplace) is functional', estimateMinutes: 15 },
  ],
  indicatorIds: ['energy_02_nat_gas_storage'],
  urgency: 'week',
};

// ═══════════════════════════════════════════════════════════════════════════
// SIGNAL LOOKUP BY DOMAIN
// ═══════════════════════════════════════════════════════════════════════════

export const SIGNAL_CONTENT_BY_DOMAIN: Record<string, SignalContent> = {
  'security_infrastructure': INFRASTRUCTURE_SIGNAL,
  'oil_axis': OIL_SECURITY_SIGNAL,
  'energy': NATURAL_GAS_SIGNAL,
  'jobs_labor': LABOR_SIGNAL,
  'economy': FINANCIAL_SIGNAL,
  'banking': BANKING_STRESS_SIGNAL,
  'housing': BANKING_STRESS_SIGNAL,
  'housing_mortgage': BANKING_STRESS_SIGNAL,
  'travel_mobility': TRAVEL_SIGNAL,
  'aviation': AVIATION_SIGNAL,
  'global_conflict': GLOBAL_CONFLICT_SIGNAL,
  'domestic_control': DOMESTIC_CONTROL_SIGNAL,
  'supply_chain': SUPPLY_CHAIN_SIGNAL,
  'water_infrastructure': WATER_INFRASTRUCTURE_SIGNAL,
  'telecom': TELECOM_SIGNAL,
  'communications': TELECOM_SIGNAL,
  'rights_governance': CIVIL_LIBERTY_SIGNAL,
  'health': HEALTH_BIOSECURITY_SIGNAL,
  'emergency': DISASTER_SIGNAL,
};

// All available signals for synthesis
export const ALL_SIGNALS: SignalContent[] = [
  INFRASTRUCTURE_SIGNAL,
  OIL_SECURITY_SIGNAL,
  LABOR_SIGNAL,
  FINANCIAL_SIGNAL,
  TRAVEL_SIGNAL,
  GLOBAL_CONFLICT_SIGNAL,
  DOMESTIC_CONTROL_SIGNAL,
  HEALTH_BIOSECURITY_SIGNAL,
  BANKING_STRESS_SIGNAL,
  SUPPLY_CHAIN_SIGNAL,
  WATER_INFRASTRUCTURE_SIGNAL,
  TELECOM_SIGNAL,
  CIVIL_LIBERTY_SIGNAL,
  AVIATION_SIGNAL,
  DISASTER_SIGNAL,
  NATURAL_GAS_SIGNAL,
];

/**
 * Get signal content based on elevated indicators
 */
export function getSignalContentForIndicators(
  _indicatorIds: string[],
  domain: string
): SignalContent | null {
  return SIGNAL_CONTENT_BY_DOMAIN[domain] || null;
}

/**
 * Generate a unique action ID for tracking completion
 */
export function generateActionId(signalId: string, index: number): string {
  return `${signalId}-action-${index}`;
}
