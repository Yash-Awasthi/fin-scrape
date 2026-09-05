/**
 * Indicator Context Map
 *
 * Rich domain knowledge for each indicator, encoding:
 * - What it means at amber/red levels
 * - Family-specific impacts
 * - What to do
 * - Peripheral impacts the headline misses
 *
 * This data enriches both the AI prompt and the fallback path.
 */

export interface IndicatorContextEntry {
  whatItMeans: { amber: string; red: string };
  familyImpact: { amber: string; red: string };
  whatToDo: { amber: string; red: string };
  dataPointLabel: string;
  source: string;
  peripheralImpacts: string[];
}

export const INDICATOR_CONTEXT: Record<string, IndicatorContextEntry> = {
  // ============================================================================
  // ECONOMY
  // ============================================================================

  'econ_01_treasury_tail': {
    whatItMeans: {
      amber: 'Treasury auctions are showing weak demand — investors are nervous about US debt',
      red: 'Treasury market stress is severe — the government is struggling to borrow at stable rates',
    },
    familyImpact: {
      amber: 'Mortgage rates and car loans will get more expensive. Credit card rates may spike.',
      red: 'Potential for banking system stress. ATMs and credit card networks could see disruptions. Interest rates on everything climb fast.',
    },
    whatToDo: {
      amber: 'Lock in any variable-rate debt. Consider moving savings to T-bills if not already.',
      red: 'Hold 2-4 weeks cash in small bills. Screenshot all bank and investment balances. Verify FDIC coverage.',
    },
    dataPointLabel: '10Y auction tail',
    source: 'Treasury Direct / Bloomberg',
    peripheralImpacts: ['Mortgage refi window closing', 'Credit card rate hikes', 'Student loan cost increases'],
  },

  'econ_02_grocery_cpi': {
    whatItMeans: {
      amber: 'Grocery prices climbing faster than normal — 3-month trend shows acceleration',
      red: 'Grocery inflation is spiking hard — expect 15-20% higher bills within weeks',
    },
    familyImpact: {
      amber: 'Weekly grocery bill going up $30-50. Specialty items and organic options hit first.',
      red: 'Real pressure on the food budget. Some items will have spot shortages. Formula and baby food affected early.',
    },
    whatToDo: {
      amber: 'Stock 2 weeks of shelf-stable essentials at current prices. Focus on what you actually eat.',
      red: 'Buy 30-day buffer of rice, beans, canned protein, and household essentials now. Prices will not come down soon.',
    },
    dataPointLabel: 'Food CPI (3mo annualized)',
    source: 'Bureau of Labor Statistics',
    peripheralImpacts: ['Baby food/formula availability', 'Pet food price jumps', 'School lunch quality drops', 'Restaurant prices follow with 4-6 week lag'],
  },

  'market_01_intraday_swing': {
    whatItMeans: {
      amber: 'Bond markets are swinging more than usual — traders are uncertain about the economy',
      red: 'Extreme bond market volatility — this is the kind of stress that preceded 2008 and COVID crashes',
    },
    familyImpact: {
      amber: 'Your 401k may fluctuate more than usual. Not a crisis, but worth watching.',
      red: 'Retirement accounts could drop 15-30%. More importantly, if bond markets seize, normal banking could be disrupted.',
    },
    whatToDo: {
      amber: 'Check your 401k allocation. Consider shifting to more conservative if retirement is <10 years away.',
      red: 'Do NOT panic sell. Screenshot all balances. Have 2 weeks cash. Check that direct deposit is working.',
    },
    dataPointLabel: '10Y intraday swing',
    source: 'Bloomberg / Treasury',
    peripheralImpacts: ['Retirement account volatility', 'Home equity line freezes', 'Small business credit tightening'],
  },

  'market_02_luxury_collapse': {
    whatItMeans: {
      amber: 'High-end retail and luxury stocks are sliding — usually a leading indicator of broader consumer weakness',
      red: 'Luxury market in freefall — historically this precedes recession by 3-6 months',
    },
    familyImpact: {
      amber: 'Job market will soften in 2-3 months, especially in tech, finance, and professional services.',
      red: 'Layoffs coming across white-collar industries. Hiring freezes likely within 4-8 weeks. Tighten spending now.',
    },
    whatToDo: {
      amber: 'Review your emergency fund. If less than 3 months expenses, start building.',
      red: 'Freeze discretionary spending. Build to 6 months cash reserve. Update resume and activate your network.',
    },
    dataPointLabel: 'Luxury stock collapse index',
    source: 'Bloomberg / S&P',
    peripheralImpacts: ['White-collar layoffs 3-6 months out', 'Freelance/contract work dries up', 'Real estate softening begins', 'Venture funding freezes'],
  },

  // ============================================================================
  // GLOBAL CONFLICT
  // ============================================================================

  'nato_high_readiness': {
    whatItMeans: {
      amber: 'NATO allies are activating high-readiness units — this is above routine exercise levels',
      red: 'NATO at maximum conventional readiness — this only happens when escalation risk is assessed as serious',
    },
    familyImpact: {
      amber: 'Oil and energy prices likely to spike 10-20% within days. Travel disruptions possible.',
      red: 'Significant risk of energy supply disruption, cyber attacks on infrastructure, and rapid price spikes across fuel, food, and goods.',
    },
    whatToDo: {
      amber: 'Fill vehicle tanks. Check generator fuel. Review family communications plan.',
      red: 'Execute priority checklist. Fill all fuel. Withdraw cash. Charge all devices. Brief family on rally points.',
    },
    dataPointLabel: 'NATO high-readiness activations',
    source: 'NATO / SHAPE',
    peripheralImpacts: ['Energy price spike', 'Cyber attacks on utilities', 'Flight cancellations/rerouting', 'Shipping insurance costs spike'],
  },

  'conf_02_russia_nato': {
    whatItMeans: {
      amber: 'Russia-NATO escalation index climbing — more provocative actions, reduced communication channels',
      red: 'Escalation index critical — near-peer conflict indicators at levels not seen since Cold War peaks',
    },
    familyImpact: {
      amber: 'Geopolitical uncertainty affects markets, energy prices, and potentially local infrastructure security.',
      red: 'This is the scenario where grid attacks, fuel disruptions, and financial system stress all become plausible simultaneously.',
    },
    whatToDo: {
      amber: 'Review Phase 3+ supplies. Ensure comms plan is current. Check GMRS radio batteries.',
      red: 'Full Phase 7 response. This is what the phases were built for. Execute from the top.',
    },
    dataPointLabel: 'Escalation index (0-100)',
    source: 'Custom composite (ACLED + NATO + OSINT)',
    peripheralImpacts: ['Potential draft discussion', 'Cyber disruption to banking/power', 'Refugee flows affecting local resources', 'School lockdown protocols activated'],
  },

  'conf_01_global_battle': {
    whatItMeans: {
      amber: 'Global battle intensity above normal — multiple active conflicts intensifying simultaneously',
      red: 'ACLED data showing conflict intensity at crisis levels — cascading regional effects likely',
    },
    familyImpact: {
      amber: 'Oil prices rise, shipping costs increase, some consumer goods become scarce. Travel advisories expand.',
      red: 'Multi-front global instability. Energy, supply chain, financial markets all affected. Domestic political tensions rise.',
    },
    whatToDo: {
      amber: 'Stay informed but don\'t doom-scroll. Focus on actionable preps: supplies, comms, fuel.',
      red: 'Review family emergency plan. Confirm everyone knows rally points. Check go-bags.',
    },
    dataPointLabel: 'ACLED battle events/day',
    source: 'ACLED (Armed Conflict Location & Event Data)',
    peripheralImpacts: ['Oil price shock', 'Shipping route disruptions', 'Refugee policy changes', 'Defense spending crowds out domestic programs'],
  },

  'conf_03_taiwan_pla': {
    whatItMeans: {
      amber: 'PLA military activity near Taiwan above normal — higher sortie rates and naval presence',
      red: 'PLA activity consistent with blockade preparation or escalation beyond posturing',
    },
    familyImpact: {
      amber: 'Tech supply chain risks: semiconductors, electronics, components. Prices on devices will rise.',
      red: 'Major supply chain crisis. Electronics, medical devices, auto parts — anything with chips gets scarce fast. Think 2021 chip shortage but 10x worse.',
    },
    whatToDo: {
      amber: 'If you need any electronics, medical devices, or appliances — buy now. Prices will climb.',
      red: 'Buy critical electronics/devices immediately. Stock any chip-dependent medications. This cascades into everything within 4-6 weeks.',
    },
    dataPointLabel: 'PLA aircraft near Taiwan (daily avg)',
    source: 'Taiwan Ministry of National Defense',
    peripheralImpacts: ['Semiconductor shortage', 'Medical device availability', 'Auto parts and repair delays', 'School tech programs affected'],
  },

  // ============================================================================
  // DOMESTIC CONTROL
  // ============================================================================

  'dom_01_ice_detention': {
    whatItMeans: {
      amber: 'ICE detention facilities filling — enforcement operations expanding to new areas',
      red: 'Detention system at capacity — historically correlates with aggressive enforcement in civilian spaces',
    },
    familyImpact: {
      amber: 'Mixed-status families and communities face increased anxiety. Workplace raids possible.',
      red: 'Enforcement operations reported in schools, hospitals, churches. Community trust breaks down. Local services disrupted.',
    },
    whatToDo: {
      amber: 'Know your rights. Ensure all family documents are accessible. Share info with affected community members.',
      red: 'Have documents on person at all times. Know your legal contacts. Have a family protocol for if someone is detained.',
    },
    dataPointLabel: 'Detention bed fill rate',
    source: 'TRAC Immigration (Syracuse University)',
    peripheralImpacts: ['School attendance drops in affected communities', 'Local business closures', 'Healthcare avoidance', 'Community resource strain'],
  },

  'dhs_removal_expansion': {
    whatItMeans: {
      amber: 'DHS expanding expedited removal to additional cities and categories',
      red: 'Expedited removal used broadly — due process erosion affecting legal residents and citizens caught in sweeps',
    },
    familyImpact: {
      amber: 'Travel within the US may involve more checkpoints. Document everything.',
      red: 'Keep passports and birth certificates accessible at all times. Know emergency legal contacts.',
    },
    whatToDo: {
      amber: 'Update go-folder with all citizenship/residency documents. Know ACLU hotline number.',
      red: 'Review relocation options. Ensure all documents are current. Have legal contacts ready.',
    },
    dataPointLabel: 'Expedited removal expansion (cities)',
    source: 'DHS / TRAC Immigration',
    peripheralImpacts: ['Family travel within US affected', 'Document readiness critical', 'Community legal resource demand spikes'],
  },

  'national_guard_metros': {
    whatItMeans: {
      amber: 'National Guard deployed to metropolitan areas for non-disaster reasons',
      red: 'Guard presence in multiple major cities — domestic security posture significantly elevated',
    },
    familyImpact: {
      amber: 'Civil unrest potential. Avoid demonstration areas. Review family rally points.',
      red: 'Movement restrictions possible in affected metros. Commute disruptions. Schools may close. This is a Phase 5 trigger.',
    },
    whatToDo: {
      amber: 'Identify alternate commute routes. Have 72-hour supplies in car. Review family comms plan.',
      red: 'Consider whether to stay or relocate temporarily. Have cash, fuel, and go-bags ready. This triggers Phase 5.',
    },
    dataPointLabel: 'Cities with Guard deployed',
    source: 'National Guard Bureau / news monitoring',
    peripheralImpacts: ['School closures', 'Public transit disruptions', 'Business closures in affected areas', 'Curfew possibility'],
  },

  // ============================================================================
  // AI WINDOW
  // ============================================================================

  'ai_01_agi_milestones': {
    whatItMeans: {
      amber: 'AI capability milestones being crossed ahead of projected timeline — autonomous agent thresholds approaching',
      red: 'Major capability jump — the kind that reshapes job markets and power structures within months, not years',
    },
    familyImpact: {
      amber: 'Job market restructuring accelerating. PM roles shifting toward AI orchestration. Entry-level positions shrinking.',
      red: 'Strategic PMs survive, operational PMs compress. Nonprofits lag further behind in AI adoption.',
    },
    whatToDo: {
      amber: 'Review your AI product positioning. Update resume with AI orchestration language.',
      red: 'Fast-track AI skills development. Position as AI adoption specialist. Accelerate side projects.',
    },
    dataPointLabel: 'Capability milestone score',
    source: 'Epoch AI / AI research publications',
    peripheralImpacts: ['Entry-level job elimination', 'Nonprofit governance vacuum', 'Education system scramble', 'Career landscape shifts'],
  },

  'ai_02_layoffs': {
    whatItMeans: {
      amber: 'AI-attributed layoffs rising — companies replacing roles rather than augmenting them',
      red: 'Mass displacement events — multiple major employers citing AI as primary driver of workforce reduction',
    },
    familyImpact: {
      amber: 'Job security requires demonstrating AI leverage, not just domain expertise. Competition for PM roles intensifies.',
      red: 'The "stratified augmentation" scenario: elite AI-native professionals gain, everyone else compresses.',
    },
    whatToDo: {
      amber: 'Document your AI-product track record. Build case studies. Strengthen network in AI-forward companies.',
      red: 'Activate multiple income streams. Diversification is survival.',
    },
    dataPointLabel: 'AI-attributed layoffs/month',
    source: 'Challenger Gray / BLS / news monitoring',
    peripheralImpacts: ['Housing market softening in tech hubs', 'Consumer spending pullback', 'Mental health crisis in displaced workers', 'Community tax base erosion'],
  },

  // ============================================================================
  // SECURITY & INFRASTRUCTURE
  // ============================================================================

  'sec_01_cisa_cve': {
    whatItMeans: {
      amber: 'CISA reporting elevated critical vulnerabilities — attack surface expanding',
      red: 'Active exploitation of critical infrastructure systems — this is Colonial Pipeline-level risk',
    },
    familyImpact: {
      amber: 'Update all devices. Change banking passwords. Enable 2FA on everything.',
      red: 'Expect service disruptions: banking, power, water, communications. Screenshot financial balances. Prepare for 24-72 hour offline period.',
    },
    whatToDo: {
      amber: 'Run all software updates. Change passwords on bank, email, and key accounts. Verify 2FA is on.',
      red: 'Screenshot all financial accounts. Download offline maps. Charge all devices. Have cash. Test GMRS radios.',
    },
    dataPointLabel: 'Critical CVEs (90-day)',
    source: 'CISA (Cybersecurity & Infrastructure Security Agency)',
    peripheralImpacts: ['Banking access disruption', 'Power grid vulnerability', 'Hospital systems at risk', 'School system data breaches'],
  },

  // ============================================================================
  // SUPPLY CHAIN
  // ============================================================================

  'supply_01_shipping_delay': {
    whatItMeans: {
      amber: 'Major shipping routes experiencing delays — goods taking longer to reach ports',
      red: 'Shipping delays severe — expect 3-6 week delays on imported goods across categories',
    },
    familyImpact: {
      amber: 'Some items may be temporarily unavailable. Holiday shopping should be done earlier.',
      red: 'Shortages in multiple product categories. Prices rising. Order anything you need now.',
    },
    whatToDo: {
      amber: 'Order any needed items early. Stock up on essentials that could face delays.',
      red: 'Buy 30-day supply of household essentials. Stock medications. Fill prescriptions to maximum.',
    },
    dataPointLabel: 'Average shipping delay (days)',
    source: 'Freightos / MarineTraffic',
    peripheralImpacts: ['Holiday gift shortages', 'Prescription medication delays', 'Auto parts unavailable', 'Construction material delays'],
  },

  'supply_02_pharmacy_shortage': {
    whatItMeans: {
      amber: 'Critical medication shortages increasing — supply chain stress reaching pharmacies',
      red: 'Widespread medication shortages — families need to act on prescriptions immediately',
    },
    familyImpact: {
      amber: 'Some medications may require substitutions. Refill timing becomes important.',
      red: 'Get all prescriptions filled to maximum allowed (90-day if possible). Some medications may be unavailable.',
    },
    whatToDo: {
      amber: 'Call pharmacy about 90-day refills for all family medications. Check OTC stock (Tylenol, Benadryl, etc.).',
      red: 'Fill every prescription NOW. Stock 30-day OTC medicine supply. Contact doctor about alternatives for anything in shortage.',
    },
    dataPointLabel: 'Critical medication shortages',
    source: 'FDA Drug Shortage Database',
    peripheralImpacts: ['Pediatric medication gaps', 'Elderly care complications', 'Mental health med shortages (SSRIs)', 'Veterinary medication affected too'],
  },

  // ============================================================================
  // OIL AXIS
  // ============================================================================

  'oil_01_hormuz_risk': {
    whatItMeans: {
      amber: 'Shipping insurance through Strait of Hormuz rising — military escorts being discussed',
      red: 'Hormuz functionally restricted — 20% of global oil transits through this strait',
    },
    familyImpact: {
      amber: 'Gas prices rising 15-25% within days. Heating oil cost increases if this persists.',
      red: 'Gas price spike of 40-60%. Heating oil becomes expensive. Fill tanks now.',
    },
    whatToDo: {
      amber: 'Fill vehicle tanks. Consider topping off heating oil.',
      red: 'Call for heating oil delivery immediately. Fill all vehicle tanks. This affects commute and heating costs significantly.',
    },
    dataPointLabel: 'War-risk insurance premium (%)',
    source: 'Lloyd\'s of London / shipping industry data',
    peripheralImpacts: ['Heating oil costs spike', 'Commute costs spike', 'Delivery service surcharges', 'Food transport costs → grocery prices'],
  },

  // ============================================================================
  // ENERGY
  // ============================================================================

  'energy_01_grid_warning': {
    whatItMeans: {
      amber: 'Grid operator issuing capacity warnings — demand approaching available supply',
      red: 'Rolling blackouts possible — grid under severe stress',
    },
    familyImpact: {
      amber: 'Power outages possible during peak hours. Charge devices before afternoon.',
      red: 'Extended outages likely. Medical equipment on battery backup. Refrigerated medications at risk.',
    },
    whatToDo: {
      amber: 'Charge all devices. Check flashlight batteries. Have candles/lanterns ready.',
      red: 'Full blackout prep. Coolers with ice for refrigerated items. Generator if available. Check on elderly neighbors.',
    },
    dataPointLabel: 'Grid capacity margin (%)',
    source: 'NERC / Regional grid operator',
    peripheralImpacts: ['Medical equipment risk', 'Food spoilage', 'Work-from-home disruption', 'School closures possible'],
  },

  // ============================================================================
  // INFORMATION WARFARE
  // ============================================================================

  'info_02_deepfake_shocks': {
    whatItMeans: {
      amber: 'Deepfake content causing market movements — information verification becoming harder',
      red: 'Major deepfake events causing panic or market crashes — trust in information breaking down',
    },
    familyImpact: {
      amber: 'Be skeptical of viral content. Verify before acting on alarming news.',
      red: 'Market volatility from false information. Verify everything through multiple sources before major decisions.',
    },
    whatToDo: {
      amber: 'Establish trusted news sources. Verify alarming claims before sharing or acting.',
      red: 'Pause before reacting to breaking news. Wait 30 minutes for verification. Don\'t make financial moves based on unverified reports.',
    },
    dataPointLabel: 'Deepfake market impact events',
    source: 'Custom monitoring / news analysis',
    peripheralImpacts: ['Market flash crashes', 'Social media panic', 'Political manipulation', 'Scam vulnerability increases'],
  },

  // ============================================================================
  // RIGHTS & GOVERNANCE
  // ============================================================================

  'rights_01_legiscan': {
    whatItMeans: {
      amber: 'AI surveillance bills accelerating through state legislatures',
      red: 'Surveillance legislation passing in multiple states simultaneously — rapid erosion of privacy protections',
    },
    familyImpact: {
      amber: 'Digital privacy increasingly compromised. Review your digital security practices.',
      red: 'Assume digital communications are monitored. Prioritize encrypted channels.',
    },
    whatToDo: {
      amber: 'Audit your digital footprint. Verify encrypted backups. Review password manager setup.',
      red: 'Activate full digital resilience plan. Encrypted comms priority. Local-only security cameras.',
    },
    dataPointLabel: 'AI surveillance bills/month',
    source: 'LegiScan / EFF Tracker',
    peripheralImpacts: ['Digital privacy erosion', 'Community organizing affected', 'Journalism implications'],
  },

  // ============================================================================
  // WATER INFRASTRUCTURE
  // ============================================================================

  'water_01_reservoir_level': {
    whatItMeans: {
      amber: 'Major reservoirs dropping below normal levels — regional water stress emerging',
      red: 'Reservoir levels critically low — mandatory water restrictions likely across multiple states',
    },
    familyImpact: {
      amber: 'Water bills likely rising. Outdoor watering restrictions may start. Stock some backup water.',
      red: 'Rationing possible. Agriculture affected means food prices spike. Some regions may need to relocate.',
    },
    whatToDo: {
      amber: 'Check your local reservoir status. Stock 3-day emergency water supply. Fix any leaks.',
      red: 'Stock 2-week water supply (1 gallon/person/day). Consider water filtration. Reduce discretionary use.',
    },
    dataPointLabel: 'Avg reservoir capacity',
    source: 'USBR / USACE',
    peripheralImpacts: ['Agricultural output drops', 'Hydropower reduced', 'Fish/wildlife collapse', 'Property values in affected areas'],
  },

  'water_02_treatment_alerts': {
    whatItMeans: {
      amber: 'Multiple water treatment alerts active — infrastructure showing stress',
      red: 'Widespread boil notices or treatment failures — tap water safety compromised in many areas',
    },
    familyImpact: {
      amber: 'Check if your water system is affected. May need to boil water for drinking.',
      red: 'Unsafe to drink tap water without treatment. Showering okay but avoid ingestion. Formula preparation affected.',
    },
    whatToDo: {
      amber: 'Stock backup bottled water. Get a quality water filter. Know your utility\'s alert system.',
      red: 'Switch to bottled water for all consumption. Boil water 1 minute if filtering. Check on elderly neighbors.',
    },
    dataPointLabel: 'Active treatment alerts',
    source: 'EPA SDWIS',
    peripheralImpacts: ['Baby formula safety', 'School closures', 'Restaurant/hospital operations', 'Pet water safety'],
  },

  'water_03_drought_monitor': {
    whatItMeans: {
      amber: 'Significant portions of US in extreme drought — agricultural stress building',
      red: 'Widespread severe drought — crop failures likely, water infrastructure strained',
    },
    familyImpact: {
      amber: 'Food prices will rise in 3-6 months. Some produce availability issues.',
      red: 'Significant food inflation coming. Wells may fail in drought areas. Fire danger extreme.',
    },
    whatToDo: {
      amber: 'Stock shelf-stable foods. Review fire insurance. Reduce outdoor water use.',
      red: 'Stock 30 days of food now. Have evacuation plan if in fire zone. Check well water if applicable.',
    },
    dataPointLabel: 'US area in extreme drought',
    source: 'US Drought Monitor',
    peripheralImpacts: ['Wildfire season intensity', 'Rural well failures', 'Cattle culling/meat prices', 'Migration from affected regions'],
  },

  // ============================================================================
  // TELECOMMUNICATIONS
  // ============================================================================

  'telecom_01_bgp_anomalies': {
    whatItMeans: {
      amber: 'Internet routing showing unusual patterns — possible attacks or misconfigurations',
      red: 'Major routing disruptions — internet connectivity issues affecting banking, communications',
    },
    familyImpact: {
      amber: 'Some websites may be slow or inaccessible. Online banking may have intermittent issues.',
      red: 'Internet services may be disrupted for hours. Online banking/payments could fail. Emergency services affected.',
    },
    whatToDo: {
      amber: 'Have cash backup. Know your bank\'s phone number. Alternative communication methods ready.',
      red: 'Use cash for transactions. Phone/text for critical communication. Wait for services to stabilize.',
    },
    dataPointLabel: 'BGP anomalies/day',
    source: 'BGPStream / CAIDA',
    peripheralImpacts: ['Online banking access', 'Credit card processing', 'Telemedicine interruptions', 'Remote work disruption'],
  },

  'telecom_02_cell_outages': {
    whatItMeans: {
      amber: 'Regional cell network outages affecting hundreds of thousands — network stress evident',
      red: 'Widespread cell outages — multiple carriers affected, 911 access compromised',
    },
    familyImpact: {
      amber: 'May not be able to reach family by cell. Check carrier status before relying on phone.',
      red: 'Cannot rely on cell phones. 911 may not work. Need backup communication plan.',
    },
    whatToDo: {
      amber: 'Establish meeting points with family. Know alternate contact methods. Keep devices charged.',
      red: 'Activate family communication plan. Use landline or WiFi calling if available. Check on neighbors.',
    },
    dataPointLabel: 'Major outages',
    source: 'Downdetector / FCC',
    peripheralImpacts: ['Emergency 911 access', 'Credit card terminals down', 'Two-factor auth fails', 'Delivery/rideshare unavailable'],
  },

  'telecom_03_undersea_cable': {
    whatItMeans: {
      amber: 'Undersea cable damage reported — international bandwidth reduced',
      red: 'Multiple cables affected — potential sabotage, significant international connectivity loss',
    },
    familyImpact: {
      amber: 'International calls/video may be slower. Overseas business connections affected.',
      red: 'Cloud services with international components may fail. Financial system connectivity at risk.',
    },
    whatToDo: {
      amber: 'Backup any cloud data locally. Have alternative communication with overseas contacts.',
      red: 'Download any critical cloud files. Expect service disruptions. Have local copies of important docs.',
    },
    dataPointLabel: 'Cable incidents',
    source: 'TeleGeography',
    peripheralImpacts: ['International business', 'Cloud service reliability', 'Financial system connectivity', 'Military/government comms'],
  },

  // ============================================================================
  // HOUSING & MORTGAGE
  // ============================================================================

  'housing_01_delinquency': {
    whatItMeans: {
      amber: 'Mortgage delinquencies rising — homeowners struggling to make payments',
      red: 'Delinquency rates at crisis levels — foreclosure wave forming',
    },
    familyImpact: {
      amber: 'Your neighborhood property values may soften. If you own, review your mortgage terms.',
      red: 'Property values may drop significantly. Neighborhood stability affected. Refinancing harder.',
    },
    whatToDo: {
      amber: 'If struggling with payments, contact lender NOW before missing. Review budget for vulnerabilities.',
      red: 'Lock in any home equity lines while available. Build cash reserves. Hold off on major home purchases.',
    },
    dataPointLabel: '90+ day delinquency rate',
    source: 'MBA / FRED',
    peripheralImpacts: ['Property tax assessments', 'Neighborhood maintenance', 'School funding', 'Local business health'],
  },

  'housing_02_foreclosure': {
    whatItMeans: {
      amber: 'Foreclosure filings rising above normal — distressed sales increasing',
      red: 'Foreclosure wave underway — housing market under severe stress',
    },
    familyImpact: {
      amber: 'May be opportunities to buy, but also risk to existing property values.',
      red: 'Widespread value declines. Selling becomes difficult. Negative equity possible.',
    },
    whatToDo: {
      amber: 'Research your local foreclosure trends. If buying, consider distressed properties.',
      red: 'Avoid selling unless necessary. Focus on paying down mortgage. Cash is king in these periods.',
    },
    dataPointLabel: 'Foreclosure filings vs baseline',
    source: 'ATTOM / RealtyTrac',
    peripheralImpacts: ['Rental market tightening', 'Construction employment', 'Bank balance sheets', 'Consumer spending'],
  },

  'housing_03_rate_shock': {
    whatItMeans: {
      amber: 'Significant wave of ARMs resetting — payment increases hitting many homeowners',
      red: 'Major ARM reset wave — widespread payment shock, default risk elevated',
    },
    familyImpact: {
      amber: 'If you have an ARM, know your reset date and potential new payment amount.',
      red: 'ARMs could see 50%+ payment increases. Many will be forced to sell or default.',
    },
    whatToDo: {
      amber: 'Refinance to fixed rate if possible. Calculate worst-case payment scenario.',
      red: 'Contact lender about modification options before reset. Build emergency fund. Know your options.',
    },
    dataPointLabel: 'ARMs resetting in 12mo',
    source: 'MBA',
    peripheralImpacts: ['Forced selling pressure', 'Rental demand spike', 'Consumer spending decline', 'Bank loss provisions'],
  },

  // ============================================================================
  // FOOD PRODUCTION
  // ============================================================================

  'food_01_crop_condition': {
    whatItMeans: {
      amber: 'Crop conditions deteriorating — yields will be below normal',
      red: 'Major crop stress — significant production losses expected',
    },
    familyImpact: {
      amber: 'Food prices rising 3-6 months out. Some items may have availability issues.',
      red: 'Significant grocery inflation coming. Staple foods affected. Budget pressure increasing.',
    },
    whatToDo: {
      amber: 'Stock up on shelf-stable versions of crops affected. Buy at current prices.',
      red: 'Build 30-day food buffer. Focus on rice, beans, flour basics. Consider bulk purchasing.',
    },
    dataPointLabel: 'Crops rated Good/Excellent',
    source: 'USDA NASS',
    peripheralImpacts: ['Animal feed costs', 'Biofuel production', 'Export restrictions', 'Farm bankruptcies'],
  },

  'food_02_livestock_disease': {
    whatItMeans: {
      amber: 'Active disease outbreaks in livestock — some culling underway',
      red: 'Widespread livestock disease — mass culling, potential zoonotic concern',
    },
    familyImpact: {
      amber: 'Specific meat prices will spike. Consider alternative proteins temporarily.',
      red: 'Major meat price increases. Eggs affected by bird flu. Some products unavailable. Zoonotic risk if severe.',
    },
    whatToDo: {
      amber: 'Stock some frozen meat at current prices. Review alternative protein sources.',
      red: 'Stock protein sources. If bird flu, avoid live poultry markets. Monitor for human transmission.',
    },
    dataPointLabel: 'Active disease alerts',
    source: 'USDA APHIS',
    peripheralImpacts: ['Pet food supply', 'Leather/byproduct industries', 'Farm community distress', 'Zoonotic transmission risk'],
  },

  'food_03_fertilizer_price': {
    whatItMeans: {
      amber: 'Fertilizer prices elevated — farmers facing higher input costs',
      red: 'Fertilizer spike — farmers will plant less, yields will drop, food prices will surge',
    },
    familyImpact: {
      amber: 'Grocery inflation 6-12 months out. Fresh produce affected first.',
      red: 'Major food price increases coming. Global food security concerns. Stock basics now.',
    },
    whatToDo: {
      amber: 'Plan garden if you have space. Stock shelf-stable foods at current prices.',
      red: 'Stock 60-90 days of food basics. Consider joining a buying club. Local farmers may have better prices.',
    },
    dataPointLabel: 'Fertilizer price vs avg',
    source: 'World Bank',
    peripheralImpacts: ['Global food prices', 'Developing world hunger', 'Agricultural employment', 'Rural community stress'],
  },

  'food_04_processing_capacity': {
    whatItMeans: {
      amber: 'Meat processing capacity reduced — supply chain bottleneck forming',
      red: 'Major processing disruption — meat shortage and price spikes imminent',
    },
    familyImpact: {
      amber: 'Meat selection may be limited. Prices rising. Buy now if you can freeze.',
      red: 'Meat shortages at stores within 1-2 weeks. Prices spike 30%+. Purchase limits likely.',
    },
    whatToDo: {
      amber: 'Stock freezer with meat at current prices. Know local butchers/farmers.',
      red: 'Alternative proteins (beans, eggs, fish). Local farms may have supply. Rationing mindset.',
    },
    dataPointLabel: 'Processing capacity',
    source: 'USDA AMS',
    peripheralImpacts: ['Fast food supply', 'School lunch programs', 'Food bank stress', 'Farmer culling losses'],
  },
};

/**
 * Get context for an indicator ID
 * Falls back to a generic entry if not found
 */
export function getIndicatorContext(indicatorId: string): IndicatorContextEntry | null {
  return INDICATOR_CONTEXT[indicatorId] || null;
}

/**
 * Get all indicator IDs that have context
 */
export function getContextualIndicatorIds(): string[] {
  return Object.keys(INDICATOR_CONTEXT);
}

/**
 * Enriched indicator for AI briefing generation
 * Combines raw data with contextual knowledge
 */
export interface EnrichedIndicator {
  id: string;
  name: string;
  domain: string;
  currentValue: number | string;
  unit: string;
  status: 'green' | 'amber' | 'red';

  // Threshold context
  thresholds: {
    green: string;
    amber: string;
    red: string;
  };

  // Trend information
  trend: 'improving' | 'worsening' | 'stable';
  trendDirection?: 'up' | 'down' | 'stable';

  // Plain English context
  meaning: string;
  householdImpact: string;
  recommendedAction: string;

  // Historical context
  historicalContext?: string;
  lastElevated?: string;

  // Peripheral impacts
  peripheralImpacts: string[];

  // Source attribution
  source: string;
  dataPointLabel: string;
}

/**
 * Import types needed for enrichment
 */
import { IndicatorData, AlertLevel } from '../../types';
import { getIndicatorDescription } from '../../data/indicatorDescriptions';

/**
 * Determine trend interpretation based on indicator direction and flag type
 */
function interpretTrend(
  trendDirection: 'up' | 'down' | 'stable' | undefined,
  greenFlag: boolean = false
): 'improving' | 'worsening' | 'stable' {
  if (!trendDirection || trendDirection === 'stable') return 'stable';

  // For green flag indicators (where higher is better), up = improving
  // For normal indicators (where higher is worse), up = worsening
  if (greenFlag) {
    return trendDirection === 'up' ? 'improving' : 'worsening';
  } else {
    return trendDirection === 'up' ? 'worsening' : 'improving';
  }
}

/**
 * Enrich a single indicator with all contextual data
 */
export function enrichIndicator(indicator: IndicatorData): EnrichedIndicator {
  const context = getIndicatorContext(indicator.id);
  const description = getIndicatorDescription(indicator.id);
  const level = indicator.status.level as AlertLevel;

  // Get appropriate context based on current level
  const meaning = level === 'red'
    ? context?.whatItMeans.red
    : level === 'amber'
    ? context?.whatItMeans.amber
    : 'Operating within normal parameters';

  const householdImpact = level === 'red'
    ? context?.familyImpact.red
    : level === 'amber'
    ? context?.familyImpact.amber
    : 'No immediate household impact';

  const recommendedAction = level === 'red'
    ? context?.whatToDo.red
    : level === 'amber'
    ? context?.whatToDo.amber
    : 'Maintain normal preparedness';

  return {
    id: indicator.id,
    name: indicator.name,
    domain: indicator.domain,
    currentValue: indicator.status.value,
    unit: indicator.unit,
    status: level === 'unknown' ? 'green' : level,

    thresholds: description?.thresholds || {
      green: 'Normal range',
      amber: 'Elevated concern',
      red: 'Critical level',
    },

    trend: interpretTrend(indicator.status.trend, indicator.greenFlag),
    trendDirection: indicator.status.trend,

    meaning: meaning || description?.whyItMatters || 'Monitoring for changes',
    householdImpact: householdImpact || 'Impact assessment pending',
    recommendedAction: recommendedAction || 'Monitor situation',

    historicalContext: description?.historicalContext,

    peripheralImpacts: context?.peripheralImpacts || [],

    source: context?.source || indicator.dataSource,
    dataPointLabel: context?.dataPointLabel || indicator.name,
  };
}

/**
 * Enrich multiple indicators, optionally filtering by status
 */
export function enrichIndicators(
  indicators: IndicatorData[],
  options: {
    includeGreen?: boolean;
    sortByPriority?: boolean;
  } = {}
): EnrichedIndicator[] {
  const { includeGreen = true, sortByPriority = true } = options;

  let filtered = indicators;

  if (!includeGreen) {
    filtered = indicators.filter(i => i.status.level !== 'green');
  }

  const enriched = filtered.map(enrichIndicator);

  if (sortByPriority) {
    // Sort by status priority: critical red > red > amber > green
    enriched.sort((a, b) => {
      const priority: Record<string, number> = { red: 3, amber: 2, green: 1 };
      return (priority[b.status] || 0) - (priority[a.status] || 0);
    });
  }

  return enriched;
}

/**
 * Get a summary of current system state for briefing generation
 */
export function getSystemSummary(indicators: IndicatorData[]): {
  overallStatus: 'green' | 'amber' | 'red';
  redCount: number;
  amberCount: number;
  greenCount: number;
  criticalIndicators: EnrichedIndicator[];
  elevatedIndicators: EnrichedIndicator[];
  affectedDomains: string[];
} {
  const redIndicators = indicators.filter(i => i.status.level === 'red');
  const amberIndicators = indicators.filter(i => i.status.level === 'amber');
  const greenIndicators = indicators.filter(i => i.status.level === 'green');

  const criticalEnriched = redIndicators.map(enrichIndicator);
  const elevatedEnriched = amberIndicators.map(enrichIndicator);

  // Determine overall status
  let overallStatus: 'green' | 'amber' | 'red' = 'green';
  if (redIndicators.length > 0) {
    overallStatus = 'red';
  } else if (amberIndicators.length > 0) {
    overallStatus = 'amber';
  }

  // Get unique affected domains
  const affectedDomains = [...new Set([
    ...redIndicators.map(i => i.domain),
    ...amberIndicators.map(i => i.domain),
  ])];

  return {
    overallStatus,
    redCount: redIndicators.length,
    amberCount: amberIndicators.length,
    greenCount: greenIndicators.length,
    criticalIndicators: criticalEnriched,
    elevatedIndicators: elevatedEnriched,
    affectedDomains,
  };
}
