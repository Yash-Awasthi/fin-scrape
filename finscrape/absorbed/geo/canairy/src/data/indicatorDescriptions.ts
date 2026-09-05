// Indicator descriptions for all 34 research indicators
export interface IndicatorDescription {
  id: string;
  name: string;
  whatWeTrack?: string;
  whyItMatters: string;
  realWorldImpact?: string;
  thresholds: {
    green: string;
    amber: string;
    red: string;
  };
  actionGuidance?: {
    green: string;
    amber: string;
    red: string;
  };
  historicalContext?: string;
  methodology?: string;
  references?: string[];
}

const descriptions: Record<string, IndicatorDescription> = {
  // ECONOMY
  econ_01_treasury_tail: {
    id: 'econ_01_treasury_tail',
    name: '10Y Auction Tail',
    whatWeTrack: 'The "tail" is the difference between the expected yield and what investors actually demand at Treasury auctions. A large tail means weak demand — buyers are requiring higher interest rates to lend money to the US government.',
    whyItMatters: 'When Treasury auctions "tail" badly, it means buyers demand higher rates — banks holding bonds lose value, lending freezes, and a banking crisis can follow within weeks.',
    realWorldImpact: 'The 2023 SVB collapse was preceded by Treasury market stress. Banks holding bonds at lower rates faced massive losses when yields spiked.',
    thresholds: {
      green: 'Normal auctions — banks stable',
      amber: 'Weak demand building — monitor bank health',
      red: 'Auction failure risk — protect deposits, increase cash',
    },
    actionGuidance: {
      green: 'No action needed. Treasury market functioning normally.',
      amber: 'Review bank exposure. Consider spreading deposits across institutions. Lock in favorable mortgage rates.',
      red: 'Increase cash on hand. Ensure deposits are within FDIC limits. Delay large financed purchases.',
    },
    historicalContext: 'Treasury auction tails above 5bp are historically rare and signal institutional stress. The March 2020 COVID crash and October 2023 bond rout both featured severe auction dysfunction.',
  },
  econ_02_grocery_cpi: {
    id: 'econ_02_grocery_cpi',
    name: 'Grocery CPI',
    whatWeTrack: 'The 3-month annualized change in the Consumer Price Index for food at home. This measures how fast grocery prices are rising compared to the same period last year.',
    whyItMatters: 'Food prices hit every family directly. Sustained >8% annualized means real purchasing power erosion — your dollar buys less each week at the store.',
    realWorldImpact: 'In 2022, grocery inflation hit 13.5% — the highest since 1979. A family of four saw weekly grocery costs increase by $50-75.',
    thresholds: {
      green: 'Normal food inflation — no action needed',
      amber: 'Prices rising faster than wages — budget accordingly',
      red: 'Food crisis territory — stock up before further spikes',
    },
    actionGuidance: {
      green: 'Shop normally. No special stocking needed.',
      amber: 'Build a 2-week buffer of shelf-stable staples. Buy in bulk when prices dip.',
      red: 'Stock 30 days of non-perishables immediately. Prioritize proteins and cooking essentials.',
    },
    historicalContext: 'Food inflation above 10% has historically triggered significant changes in shopping behavior and increased food bank usage by 30-40%.',
  },
  market_01_intraday_swing: {
    id: 'market_01_intraday_swing',
    name: '10Y Intraday Swing',
    whyItMatters: 'A >=30bp single-day swing in the 10-year yield signals institutional panic. This preceded the 2023 SVB collapse and 2020 COVID crash.',
    thresholds: {
      green: 'Normal volatility — markets orderly',
      amber: 'Elevated moves — institutions repositioning',
      red: 'Systemic stress — immediate protective action required',
    },
  },
  green_g1_gdp_rates: {
    id: 'green_g1_gdp_rates',
    name: 'GDP Green Flag',
    whyItMatters: 'When GDP is strong AND yields are low, the economy is genuinely healthy. This is the signal to relax preparedness.',
    thresholds: {
      green: 'Economy strong — relax 10% of prep budget',
      amber: 'Mixed signals — maintain current readiness',
      red: 'N/A — positive indicator only',
    },
  },

  // JOBS & LABOR
  job_01_strike_days: {
    id: 'job_01_strike_days',
    name: 'US Strike Days',
    whyItMatters: 'Mass strike activity signals deep labor unrest. When workers walk off en masse, supply chains break and essential services can halt.',
    thresholds: {
      green: 'Normal labor relations',
      amber: 'Significant strike activity — supply disruptions possible',
      red: 'Mass work stoppages — essential services at risk',
    },
  },

  // RIGHTS & GOVERNANCE
  power_01_ai_surveillance: {
    id: 'power_01_ai_surveillance',
    name: 'AI Surveillance Bills',
    whyItMatters: 'Legislative proposals for AI-powered surveillance indicate expanding state control over daily life.',
    thresholds: {
      green: 'Normal legislative activity',
      amber: 'Accelerating surveillance legislation — review digital privacy',
      red: 'Surveillance state acceleration — harden digital footprint',
    },
  },
  civil_01_acled_protests: {
    id: 'civil_01_acled_protests',
    name: 'US Protests (7d avg)',
    whyItMatters: 'Rising protest frequency signals social fractures. At high levels, movement restrictions and Guard deployments follow.',
    thresholds: {
      green: 'Normal civic activity',
      amber: 'Elevated unrest — avoid protest zones',
      red: 'Social crisis — expect movement restrictions',
    },
  },

  // SECURITY & INFRASTRUCTURE
  cyber_01_cisa_kev: {
    id: 'cyber_01_cisa_kev',
    name: 'CISA KEV + ICS',
    whatWeTrack: 'The number of actively exploited cybersecurity vulnerabilities that CISA has flagged in the past 90 days, with emphasis on Industrial Control Systems (ICS) that run water plants, power grids, and pipelines.',
    whyItMatters: 'CISA flags actively exploited vulnerabilities in critical infrastructure. High counts mean water, power, and financial systems are under attack.',
    realWorldImpact: 'The 2021 Colonial Pipeline ransomware attack caused fuel shortages across the East Coast for a week. The Oldsmar water treatment hack nearly poisoned a Florida town.',
    thresholds: {
      green: 'Low exploit activity',
      amber: 'Elevated cyber attacks on infrastructure',
      red: 'Critical infrastructure under sustained attack',
    },
    actionGuidance: {
      green: 'Keep devices updated. Use strong passwords with 2FA.',
      amber: 'Update all devices immediately. Enable 2FA everywhere. Have cash on hand in case banking systems go offline.',
      red: 'Prepare for service disruptions. Fill gas tanks. Have offline copies of important documents. Stock water.',
    },
    historicalContext: 'Critical infrastructure attacks have increased 300% since 2020. Russia, China, and Iran have demonstrated capability to disrupt US power grids.',
  },
  grid_01_pjm_outages: {
    id: 'grid_01_pjm_outages',
    name: 'PJM Grid Outages',
    whatWeTrack: 'Major power outage events per quarter in the PJM Interconnection region, which serves 65 million people in 13 states from Illinois to New Jersey, including major cities like Chicago, Philadelphia, and Washington DC.',
    whyItMatters: 'Repeated large outages signal grid fragility. When this goes red, backup power is essential.',
    realWorldImpact: 'The 2021 Texas grid collapse left 4.5 million without power for days. Over 200 people died from cold exposure and carbon monoxide poisoning from improper heater use.',
    thresholds: {
      green: 'Grid stable',
      amber: 'Pattern emerging — test backup power',
      red: 'Grid fragile — activate generator prep',
    },
    actionGuidance: {
      green: 'Maintain standard emergency supplies.',
      amber: 'Test backup power systems. Charge all battery packs. Know where flashlights and candles are located.',
      red: 'Run generator to verify function. Fill propane/gas. Ensure medical devices have battery backup. Know warming center locations.',
    },
    historicalContext: 'Grid reliability has declined 15% since 2000 due to aging infrastructure and increased extreme weather. Winter storm outages have doubled since 2015.',
  },
  bio_01_h2h_countries: {
    id: 'bio_01_h2h_countries',
    name: 'Novel H2H Pathogen',
    whatWeTrack: 'The number of countries reporting sustained human-to-human transmission of novel pathogens that the WHO has flagged as concerning. This is the earliest warning system for pandemics.',
    whyItMatters: 'Novel H2H transmission in multiple countries is how pandemics start. Early detection gives weeks of preparation.',
    realWorldImpact: 'COVID-19 was first reported to the WHO on December 31, 2019. By mid-January, cases appeared in Thailand and Japan. Families who acted in January were better prepared than those who waited.',
    thresholds: {
      green: 'No novel H2H events',
      amber: 'Emerging pathogen — verify N95 and med supply',
      red: 'Pandemic risk — activate health protocols',
    },
    actionGuidance: {
      green: 'Maintain standard first aid supplies and common medications.',
      amber: 'Stock N95 masks and hand sanitizer. Refill prescriptions to 90-day supply. Review remote work/school options.',
      red: 'Limit non-essential travel and gatherings. Ensure 30-day medication supply. Prepare for potential school closures and remote work.',
    },
    historicalContext: 'Three novel pathogens have reached pandemic potential since 2000: SARS (2003), H1N1 (2009), and COVID-19 (2020). Early warning provides 2-4 weeks of preparation advantage.',
  },

  // OIL AXIS
  oil_01_russian_brics: {
    id: 'oil_01_russian_brics',
    name: 'Russian Crude to BRICS',
    whyItMatters: 'As more Russian oil flows to BRICS outside USD settlement, dollar dominance erodes.',
    thresholds: {
      green: 'Normal trade patterns',
      amber: 'De-dollarization accelerating',
      red: 'Major trade realignment — USD at risk',
    },
  },
  oil_02_mbridge_settlements: {
    id: 'oil_02_mbridge_settlements',
    name: 'mBridge Settlement',
    whyItMatters: 'China\'s mBridge CBDC settling oil trades bypasses SWIFT entirely. High volumes mean the dollar\'s oil monopoly is breaking.',
    thresholds: {
      green: 'Minimal CBDC oil settlement',
      amber: 'Growing mBridge adoption',
      red: 'Significant oil trade bypassing USD',
    },
  },
  ofac_01_designations: {
    id: 'ofac_01_designations',
    name: 'OFAC Designations',
    whyItMatters: 'Sanctions on Indian/Chinese oil entities signal escalating economic warfare that can boomerang into higher energy prices.',
    thresholds: {
      green: 'No new oil-related sanctions',
      amber: 'Sanctions activity increasing',
      red: 'Sanctions escalation — fuel prices likely to spike',
    },
  },
  oil_04_refinery_ratio: {
    id: 'oil_04_refinery_ratio',
    name: 'Refinery Run Ratio',
    whyItMatters: 'When India+China refine more than OECD, petroleum supply shifts East. Western fuel availability suffers.',
    thresholds: {
      green: 'Balanced global refining',
      amber: 'Eastern refining dominance growing',
      red: 'OECD refining deficit — shortages possible',
    },
  },

  // AI WINDOW
  labor_ai_01_layoffs: {
    id: 'labor_ai_01_layoffs',
    name: 'AI-Linked Layoffs',
    whyItMatters: 'Mass layoffs citing AI replacement signal structural job displacement.',
    thresholds: {
      green: 'Normal automation attrition',
      amber: 'AI displacement accelerating — upskill',
      red: 'Mass displacement — multiple industries affected',
    },
  },
  cyber_02_ai_ransomware: {
    id: 'cyber_02_ai_ransomware',
    name: 'AI Ransomware',
    whyItMatters: 'AI-generated ransomware is faster, smarter, and harder to stop. Rising incidents mean hospitals, utilities, and banks face downtime.',
    thresholds: {
      green: 'Low AI-assisted attacks',
      amber: 'AI ransomware increasing — verify backups',
      red: 'Infrastructure under AI-assisted attack',
    },
  },
  info_02_deepfake_shocks: {
    id: 'info_02_deepfake_shocks',
    name: 'Deepfake Market Shocks',
    whyItMatters: 'Deepfake videos of officials can crash markets in minutes. Combined with market volatility, damage compounds instantly.',
    thresholds: {
      green: 'No deepfake market events',
      amber: 'Deepfake event detected — verify news before acting',
      red: 'Information warfare active (jump to Phase 7 if Market also red)',
    },
  },
  compute_01_training_cost: {
    id: 'compute_01_training_cost',
    name: 'Training Cost Trend',
    whyItMatters: 'Rapidly falling AI training costs mean AI tools become widely accessible. This is a positive indicator.',
    thresholds: {
      green: 'Costs falling fast — AI democratizing (good)',
      amber: 'Cost reduction slowing',
      red: 'N/A — green-flag indicator',
    },
  },

  // GLOBAL CONFLICT
  global_conflict_intensity: {
    id: 'global_conflict_intensity',
    name: 'Global Battle Intensity',
    whyItMatters: 'Rising global battle events mean more supply chain disruptions and risk of great-power involvement.',
    thresholds: {
      green: 'Baseline conflict levels',
      amber: 'Multiple active conflicts escalating',
      red: 'Global conflict at dangerous levels',
    },
  },
  taiwan_pla_activity: {
    id: 'taiwan_pla_activity',
    name: 'Taiwan PLA Incursions',
    whyItMatters: 'Taiwan produces 92% of advanced chips. PLA incursions above 50/day signal rehearsal for blockade.',
    thresholds: {
      green: 'Routine ADIZ activity',
      amber: 'Elevated PLA presence — semiconductor risk',
      red: 'Blockade rehearsal — electronics shortage imminent',
    },
  },
  nato_high_readiness: {
    id: 'nato_high_readiness',
    name: 'NATO High Readiness',
    whyItMatters: 'NATO force activations only happen when Article 5 scenarios are considered plausible.',
    thresholds: {
      green: 'No readiness activations',
      amber: 'Partial activation — tensions high',
      red: 'Full activation — conflict imminent (jump to Phase 6+)',
    },
  },
  nuclear_01_tests: {
    id: 'nuclear_01_tests',
    name: 'Nuclear/Missile Tests',
    whyItMatters: 'Nuclear tests and ICBM launches signal deterrence failure risk.',
    thresholds: {
      green: 'Low test activity',
      amber: 'Increased testing — arms race dynamics',
      red: 'Rapid escalation — nuclear posture deteriorating',
    },
  },
  russia_nato_escalation: {
    id: 'russia_nato_escalation',
    name: 'Russia-NATO Index',
    whyItMatters: 'Composite tracking troop movements, rhetoric, and incidents. Above 75 means miscalculation risk is extreme.',
    thresholds: {
      green: 'Normal baseline',
      amber: 'Escalatory signals increasing',
      red: 'Crisis-level tensions',
    },
  },
  defense_spending_growth: {
    id: 'defense_spending_growth',
    name: 'Defense Spending Growth',
    whyItMatters: 'Global defense spending >8% signals arms race dynamics.',
    thresholds: {
      green: 'Normal defense budgets',
      amber: 'Arms race dynamics emerging',
      red: 'Wartime spending patterns',
    },
  },

  // DOMESTIC CONTROL
  dc_control_countdown: {
    id: 'dc_control_countdown',
    name: 'DC Autonomy Countdown',
    whyItMatters: 'Federal takeover of DC governance signals concentration of executive power.',
    thresholds: {
      green: 'DC autonomy secure',
      amber: 'Legislation advancing',
      red: 'Imminent federal takeover',
    },
  },
  national_guard_metros: {
    id: 'national_guard_metros',
    name: 'Guard Metro Deployments',
    whyItMatters: 'National Guard in major cities means civil order has broken down. Phase 5+ territory.',
    thresholds: {
      green: 'No urban deployments',
      amber: '1 metro affected',
      red: '2+ metros — systemic crisis (jump to Phase 5)',
    },
  },
  ice_detention_surge: {
    id: 'ice_detention_surge',
    name: 'ICE Detention Population',
    whyItMatters: 'Detention surges indicate mass enforcement affecting communities and local economies.',
    thresholds: {
      green: 'Normal detention levels',
      amber: 'Elevated enforcement',
      red: 'Mass detention operations',
    },
  },
  dhs_removal_expansion: {
    id: 'dhs_removal_expansion',
    name: 'DHS Expedited Removal',
    whyItMatters: 'Expansion of expedited removal reduces due process. Binary civil liberties tripwire.',
    thresholds: {
      green: 'Standard removal authority',
      amber: 'N/A — binary indicator',
      red: 'Expanded authority active (jump to Phase 5)',
    },
  },
  hill_control_legislation: {
    id: 'hill_control_legislation',
    name: 'Control Bills Advancing',
    whyItMatters: 'Bills expanding surveillance or restricting movement signal democratic backsliding.',
    thresholds: {
      green: 'Normal legislative volume',
      amber: 'Accelerating control legislation',
      red: 'Legislative assault on civil liberties',
    },
  },
  liberty_litigation_count: {
    id: 'liberty_litigation_count',
    name: 'Liberty Cases Active',
    whyItMatters: 'Active ACLU/EFF cases measure how many civil liberty fights are happening simultaneously.',
    thresholds: {
      green: 'Baseline litigation',
      amber: 'Elevated liberty challenges',
      red: 'Rights under broad legal assault',
    },
  },

  // CULT SIGNALS
  cult_trend_01_twitter: {
    id: 'cult_trend_01_twitter',
    name: '#AIGod / #Basilisk Tweets',
    whyItMatters: 'Viral AI-worship hashtags signal cult formation around AI systems.',
    thresholds: {
      green: 'Background noise',
      amber: 'Viral growth detected',
      red: 'Mass adoption — cult formation underway',
    },
  },
  cult_meme_01_tokens: {
    id: 'cult_meme_01_tokens',
    name: 'Cult ERC-20 Tokens',
    whyItMatters: 'Crypto tokens with cult+AI branding channel real money into cult ecosystems.',
    thresholds: {
      green: 'Minimal token creation',
      amber: 'Token proliferation',
      red: 'Cult economy forming on-chain',
    },
  },
  cult_event_01_protests: {
    id: 'cult_event_01_protests',
    name: 'AI Cult Protests',
    whyItMatters: 'Physical protests around AI worship indicate the movement has jumped to real-world action.',
    thresholds: {
      green: 'No cult protests',
      amber: 'Scattered cult protests',
      red: 'Organized cult movement',
    },
  },
  cult_media_01_trends: {
    id: 'cult_media_01_trends',
    name: 'AI Religion Trends',
    whyItMatters: 'Google Trends for "AI religion" captures mainstream cultural shift.',
    thresholds: {
      green: 'Low cultural penetration',
      amber: 'Growing mainstream interest',
      red: 'Mainstream cultural shift underway',
    },
  },

  // BANKING STRESS (Critical for financial briefings)
  bank_01_failures: {
    id: 'bank_01_failures',
    name: 'Bank Failures',
    whyItMatters: 'Bank failures signal systemic stress. SVB\'s collapse in March 2023 froze $175B in deposits overnight. When banks fail, ATMs can shut down, wire transfers halt, and direct deposits may not arrive.',
    thresholds: {
      green: 'No bank failures — banking system stable',
      amber: 'Small bank failures — monitor your bank\'s health',
      red: 'Major bank failures — withdraw emergency cash NOW',
    },
    historicalContext: 'March 2023: SVB, Signature, First Republic failed within weeks. 2008: 25 banks failed in crisis year.',
  },
  bank_02_discount_window: {
    id: 'bank_02_discount_window',
    name: 'Fed Discount Window',
    whyItMatters: 'Banks borrowing from the Fed\'s emergency window means they can\'t get funds elsewhere. This is the banking system\'s "911 call." High borrowing preceded both the 2008 crisis and March 2023 bank runs.',
    thresholds: {
      green: 'Low emergency borrowing — banks healthy',
      amber: 'Elevated borrowing — banks under stress',
      red: 'Emergency levels — banking crisis imminent',
    },
    historicalContext: 'Discount window borrowing spiked to $153B in March 2023, highest since 2008 crisis.',
  },
  bank_03_deposit_flow: {
    id: 'bank_03_deposit_flow',
    name: 'Bank Deposit Flows',
    whyItMatters: 'Money fleeing banks is the clearest sign of a bank run in progress. Deposits leaving your bank mean the bank may not have cash when you need it.',
    thresholds: {
      green: 'Normal deposit levels',
      amber: 'Deposits declining — early warning sign',
      red: 'Mass deposit outflows — your bank may be at risk',
    },
  },

  // JOBS & LABOR
  job_01_jobless_claims: {
    id: 'job_01_jobless_claims',
    name: 'Initial Jobless Claims',
    whyItMatters: 'Weekly unemployment claims are the earliest signal of job market health. Rising claims mean layoffs are spreading — your industry could be next.',
    thresholds: {
      green: 'Claims low — job market healthy',
      amber: 'Claims rising — layoffs spreading',
      red: 'Claims spiking — major recession signal',
    },
    historicalContext: 'COVID: Claims hit 6.8M in one week (April 2020). Recessions typically see sustained 400K+ claims.',
  },

  // FLIGHT & TRAVEL
  flight_01_ground_stops: {
    id: 'flight_01_ground_stops',
    name: 'FAA Ground Stops',
    whyItMatters: 'Ground stops halt all flights to an airport. System-wide stops signal major infrastructure failure — your travel plans could be stranded for days.',
    thresholds: {
      green: 'Normal operations',
      amber: 'Regional ground stops — check your flights',
      red: 'System-wide ground stops — travel severely disrupted',
    },
    historicalContext: 'January 2023: FAA system outage caused first nationwide ground stop since 9/11.',
  },
  flight_02_delay_pct: {
    id: 'flight_02_delay_pct',
    name: 'Flight Delay Rate',
    whyItMatters: 'High delay rates mean the system is stressed. Beyond 25%, cascading failures are likely — book backup options.',
    thresholds: {
      green: 'Normal delays (<15%)',
      amber: 'Elevated delays (15-25%) — build buffer time',
      red: 'Systemic delays (>25%) — expect cancellations',
    },
  },
  flight_03_tfr_count: {
    id: 'flight_03_tfr_count',
    name: 'Temporary Flight Restrictions',
    whyItMatters: 'TFRs indicate security events or disasters. High counts mean airspace is being controlled — major events are happening.',
    thresholds: {
      green: 'Normal TFR count',
      amber: 'Elevated restrictions — security events active',
      red: 'Widespread restrictions — major security situation',
    },
  },
  travel_01_advisories: {
    id: 'travel_01_advisories',
    name: 'Travel Advisories',
    whyItMatters: 'State Department advisories indicate where Americans face elevated risk. "Do Not Travel" means evacuate or don\'t go.',
    thresholds: {
      green: 'Few high-level advisories',
      amber: 'Multiple Level 3-4 advisories',
      red: 'Widespread "Do Not Travel" warnings',
    },
  },
  travel_02_border_wait: {
    id: 'travel_02_border_wait',
    name: 'Border Wait Times',
    whyItMatters: 'Long border waits signal enforcement surges or closures. If you live near the border or have cross-border needs, plan accordingly.',
    thresholds: {
      green: 'Normal processing times',
      amber: 'Extended waits (2-4 hours)',
      red: 'Severe delays or closures',
    },
  },
  travel_03_tsa_throughput: {
    id: 'travel_03_tsa_throughput',
    name: 'TSA Passenger Volume',
    whyItMatters: 'TSA numbers show real travel demand. Sharp drops indicate people are avoiding travel — a leading indicator of fear.',
    thresholds: {
      green: 'Normal passenger volumes',
      amber: 'Declining travel (-20-40%)',
      red: 'Travel collapse (-40%+) — major event',
    },
  },

  // ENERGY
  spr_01_level: {
    id: 'spr_01_level',
    name: 'Strategic Petroleum Reserve',
    whyItMatters: 'The SPR is America\'s emergency fuel supply. When it drops below 400M barrels, we have less cushion for oil shocks. Low reserves mean higher prices when crises hit.',
    thresholds: {
      green: 'Reserves adequate (>450M barrels)',
      amber: 'Reserves declining (350-450M)',
      red: 'Critically low (<350M) — fuel prices vulnerable',
    },
    historicalContext: 'SPR fell to 372M barrels in 2023 — lowest since 1984. Used to combat 2022 gas price spike.',
  },
  energy_02_nat_gas_storage: {
    id: 'energy_02_nat_gas_storage',
    name: 'Natural Gas Storage',
    whyItMatters: 'Gas storage levels determine winter heating costs. Low storage before winter means price spikes — budget for 2-3x heating bills.',
    thresholds: {
      green: 'Storage above 5-year average',
      amber: 'Storage below average — expect higher bills',
      red: 'Critical shortage — heating cost crisis likely',
    },
  },
  energy_03_grid_emergency: {
    id: 'energy_03_grid_emergency',
    name: 'Grid Emergency Alerts',
    whyItMatters: 'Grid emergency alerts mean blackouts are possible. Your household should activate backup power plans.',
    thresholds: {
      green: 'No grid emergencies',
      amber: 'Watch alerts — have backups ready',
      red: 'Rolling blackouts likely — activate backup power',
    },
    historicalContext: 'February 2021 Texas freeze: 4.5M homes lost power for days. 246 people died.',
  },
  oil_03_jodi_inventory: {
    id: 'oil_03_jodi_inventory',
    name: 'Global Oil Inventories',
    whyItMatters: 'JODI tracks worldwide oil stocks. Declining global inventories mean less buffer against supply shocks — prices will spike faster.',
    thresholds: {
      green: 'Global inventories stable',
      amber: 'Inventories declining',
      red: 'Critical shortage — price spike imminent',
    },
  },

  // SUPPLY CHAIN
  supply_01_port_congestion: {
    id: 'supply_01_port_congestion',
    name: 'Port Congestion',
    whyItMatters: '40% of US imports flow through LA/Long Beach. Ships waiting offshore mean empty shelves in 2-3 weeks. Stock up before shortages hit.',
    thresholds: {
      green: 'Ports flowing normally',
      amber: 'Ships backing up — order essentials now',
      red: 'Major congestion — expect shortages',
    },
    historicalContext: '2021: 100+ ships waited offshore LA. Led to holiday supply shortages and inflation spike.',
  },
  supply_02_freight_index: {
    id: 'supply_02_freight_index',
    name: 'Freight Rate Index',
    whyItMatters: 'Shipping costs flow directly to store prices. When container rates spike, consumer prices follow 2-3 months later.',
    thresholds: {
      green: 'Normal freight rates',
      amber: 'Rates rising — imported goods will cost more',
      red: 'Rate spike — significant price increases coming',
    },
    historicalContext: '2021: Container rates went from $2K to $20K. Drove 2022 inflation surge.',
  },
  supply_03_chip_lead_time: {
    id: 'supply_03_chip_lead_time',
    name: 'Semiconductor Lead Time',
    whyItMatters: 'Chips are in everything — cars, phones, appliances. Long lead times mean product shortages and price hikes.',
    thresholds: {
      green: 'Normal lead times (10-15 weeks)',
      amber: 'Extended (15-25 weeks) — expect delays',
      red: 'Severe shortage (25+ weeks) — buy now if needed',
    },
    historicalContext: '2021: Auto plants shut down due to chip shortage. New car prices rose 12%.',
  },
  supply_pharmacy_shortage: {
    id: 'supply_pharmacy_shortage',
    name: 'Drug Shortages',
    whyItMatters: 'FDA tracks active drug shortages. Your medications may become unavailable — talk to your doctor about alternatives.',
    thresholds: {
      green: 'Few critical shortages',
      amber: 'Multiple shortages — check your meds',
      red: 'Widespread shortages — secure supply',
    },
    historicalContext: 'Ozempic/Adderall shortages in 2023 affected millions. Some lasted 18+ months.',
  },

  // GLOBAL CONFLICT
  hormuz_war_risk: {
    id: 'hormuz_war_risk',
    name: 'Hormuz War Risk Premium',
    whyItMatters: '21% of world oil flows through the Strait of Hormuz. Rising insurance premiums signal shipping fears — oil prices will follow.',
    thresholds: {
      green: 'Normal insurance rates',
      amber: 'Risk premium rising — oil price pressure',
      red: 'Major premium spike — disruption expected',
    },
    historicalContext: 'Iran tensions in 2019 caused tanker attacks and brief oil price spikes.',
  },
  taiwan_exclusion_zone: {
    id: 'taiwan_exclusion_zone',
    name: 'Taiwan Exclusion Zones',
    whyItMatters: 'China establishing exclusion zones around Taiwan would signal blockade preparation. Taiwan makes 92% of advanced chips — expect global tech shortages.',
    thresholds: {
      green: 'No exclusion zones',
      amber: 'Zones declared — semiconductor risk HIGH',
      red: 'Blockade imminent — buy electronics NOW',
    },
  },

  // DOMESTIC GOVERNANCE
  power_02_dod_autonomy: {
    id: 'power_02_dod_autonomy',
    name: 'DoD AI Autonomy',
    whyItMatters: 'Policies allowing autonomous weapons systems indicate reduced human oversight over lethal force.',
    thresholds: {
      green: 'Human-in-loop required',
      amber: 'Human-on-loop being debated',
      red: 'Autonomous weapons authorized',
    },
  },
  education_01_closures: {
    id: 'education_01_closures',
    name: 'School Closures',
    whyItMatters: 'Mass school closures affect child care and family routines. May indicate pandemic, unrest, or budget crises.',
    thresholds: {
      green: 'Normal operations',
      amber: 'Some districts affected — check yours',
      red: 'Widespread closures — backup childcare needed',
    },
  },
  liberty_01_litigation: {
    id: 'liberty_01_litigation',
    name: 'Civil Rights Litigation',
    whyItMatters: 'Rising ACLU/civil rights lawsuits indicate rights are being tested. Know your rights and document interactions.',
    thresholds: {
      green: 'Baseline litigation',
      amber: 'Elevated challenges — rights under pressure',
      red: 'Rights under broad assault',
    },
  },
  luxury_01_collapse: {
    id: 'luxury_01_collapse',
    name: 'Luxury Market Collapse',
    whyItMatters: 'Luxury spending is a leading indicator — when wealthy consumers cut back, recession follows. Tighten your budget.',
    thresholds: {
      green: 'Luxury market healthy',
      amber: 'High-end spending declining',
      red: 'Luxury collapse — recession likely',
    },
  },

  // WATER INFRASTRUCTURE
  water_01_reservoir_level: {
    id: 'water_01_reservoir_level',
    name: 'Major Reservoir Levels',
    whyItMatters: 'Major reservoirs supply drinking water and irrigation for millions. Low levels mean water restrictions, higher prices, and potential rationing. Lake Mead dropping exposed 2021 water crisis.',
    thresholds: {
      green: 'Reservoirs healthy (>70%)',
      amber: 'Levels declining — expect water restrictions',
      red: 'Critical shortage — rationing likely',
    },
    historicalContext: '2022: Lake Mead hit lowest level since 1937. Mandatory cuts to Arizona, Nevada.',
  },
  water_02_treatment_alerts: {
    id: 'water_02_treatment_alerts',
    name: 'Water Treatment Alerts',
    whyItMatters: 'Boil notices and treatment failures mean your tap water may not be safe. Stock bottled water and water filters.',
    thresholds: {
      green: 'No significant alerts',
      amber: 'Multiple regions affected — check your utility',
      red: 'Widespread alerts — secure water supply',
    },
    historicalContext: 'Jackson MS 2022: 150K lost water for weeks after treatment failure.',
  },
  water_03_drought_monitor: {
    id: 'water_03_drought_monitor',
    name: 'Extreme Drought Coverage',
    whyItMatters: 'Extreme drought destroys crops, kills livestock, and depletes aquifers. Food prices spike, and some regions may become uninhabitable.',
    thresholds: {
      green: 'Drought minimal (<10% US)',
      amber: 'Significant drought (10-25%)',
      red: 'Crisis-level drought — food supply at risk',
    },
    historicalContext: '2012 drought covered 65% of US, caused $30B in crop losses.',
  },

  // TELECOMMUNICATIONS
  telecom_01_bgp_anomalies: {
    id: 'telecom_01_bgp_anomalies',
    name: 'Internet Routing Anomalies',
    whyItMatters: 'BGP hijacks can redirect or intercept internet traffic. Major anomalies can take down banking, communications, and emergency services.',
    thresholds: {
      green: 'Internet routing stable',
      amber: 'Anomalies detected — monitor services',
      red: 'Major routing disruption — expect outages',
    },
    historicalContext: 'Pakistan 2008: Accidentally took YouTube offline globally for hours.',
  },
  telecom_02_cell_outages: {
    id: 'telecom_02_cell_outages',
    name: 'Cell Network Outages',
    whyItMatters: 'Major cell outages cut off communication and 911 access. Have backup communication plans (landline, radio, neighbor coordination).',
    thresholds: {
      green: 'Networks operational',
      amber: 'Regional outages — check your carrier',
      red: 'Widespread outages — activate backup comms',
    },
    historicalContext: 'AT&T Feb 2024: 70K+ lost service for hours. 911 calls failed.',
  },
  telecom_03_undersea_cable: {
    id: 'telecom_03_undersea_cable',
    name: 'Undersea Cable Incidents',
    whyItMatters: '95% of international data flows through undersea cables. Damage isolates regions and can be act of sabotage. Russia has mapped all cables.',
    thresholds: {
      green: 'No active incidents',
      amber: 'Cable damage reported — international bandwidth reduced',
      red: 'Multiple cables affected — potential sabotage',
    },
    historicalContext: 'Red Sea 2024: Houthi attacks threatened 25% of Asia-Europe bandwidth.',
  },

  // HOUSING & MORTGAGE
  housing_01_delinquency: {
    id: 'housing_01_delinquency',
    name: 'Mortgage Delinquency',
    whyItMatters: 'Rising delinquencies precede foreclosure waves. If your neighbors can\'t pay, your property value drops. Check your mortgage options.',
    thresholds: {
      green: 'Delinquencies stable (<2%)',
      amber: 'Rising delinquencies — housing stress building',
      red: 'Crisis levels — foreclosure wave coming',
    },
    historicalContext: '2009: Delinquency hit 10%. Foreclosures devastated neighborhoods.',
  },
  housing_02_foreclosure: {
    id: 'housing_02_foreclosure',
    name: 'Foreclosure Activity',
    whyItMatters: 'Foreclosures flood the market with cheap homes, dragging down all property values. May signal economic opportunity or neighborhood decline.',
    thresholds: {
      green: 'Foreclosures below normal',
      amber: 'Activity rising — housing market stressed',
      red: 'Foreclosure wave — property values at risk',
    },
    historicalContext: '2010: 2.9M foreclosure filings. Median home price dropped 30%.',
  },
  housing_03_rate_shock: {
    id: 'housing_03_rate_shock',
    name: 'ARM Reset Exposure',
    whyItMatters: 'Adjustable-rate mortgages resetting at higher rates cause payment shock. Homeowners may face 50%+ payment increases.',
    thresholds: {
      green: 'Few resets coming',
      amber: 'Significant reset wave ahead — refinance if possible',
      red: 'Major payment shock wave — defaults likely',
    },
    historicalContext: '2007: ARM resets triggered the subprime crisis cascade.',
  },

  // FOOD PRODUCTION
  food_01_crop_condition: {
    id: 'food_01_crop_condition',
    name: 'US Crop Health',
    whyItMatters: 'Poor crop conditions mean lower yields and higher grocery prices 3-6 months later. Stock staples before price spikes.',
    thresholds: {
      green: 'Crops healthy (60%+ Good/Excellent)',
      amber: 'Crops stressed — prices will rise',
      red: 'Crop failure — stock up now',
    },
    historicalContext: '2012 drought: Corn yields dropped 27%. Food prices spiked 2013.',
  },
  food_02_livestock_disease: {
    id: 'food_02_livestock_disease',
    name: 'Livestock Disease Alerts',
    whyItMatters: 'Avian flu, African swine fever, and other diseases can wipe out herds. Meat prices spike, and zoonotic diseases may spread to humans.',
    thresholds: {
      green: 'No major outbreaks',
      amber: 'Active outbreak — expect meat price increases',
      red: 'Widespread disease — supply disruption likely',
    },
    historicalContext: '2015 bird flu: 50M birds killed. Egg prices doubled.',
  },
  food_03_fertilizer_price: {
    id: 'food_03_fertilizer_price',
    name: 'Fertilizer Costs',
    whyItMatters: 'Fertilizer drives crop yields. When prices spike, farmers plant less, and food prices follow 6-12 months later.',
    thresholds: {
      green: 'Prices near average',
      amber: 'Prices elevated — food inflation coming',
      red: 'Price spike — expect grocery increases',
    },
    historicalContext: '2022: Russia/Ukraine war tripled fertilizer prices. Global food crisis followed.',
  },
  food_04_processing_capacity: {
    id: 'food_04_processing_capacity',
    name: 'Meat Processing Capacity',
    whyItMatters: 'Only 4 companies process 85% of US beef. When plants shut down, meat disappears from shelves within days.',
    thresholds: {
      green: 'Capacity normal (>90%)',
      amber: 'Capacity reduced — meat prices rising',
      red: 'Critical shortage — empty shelves possible',
    },
    historicalContext: 'COVID 2020: Plant closures caused meat shortages. Beef prices up 20%.',
  },
};

export function getIndicatorDescription(id: string): IndicatorDescription | null {
  return descriptions[id] || null;
}
