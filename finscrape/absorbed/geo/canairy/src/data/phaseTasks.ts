/**
 * Phase Tasks - Complete Tier System
 *
 * Maps phases 0-9 into 6 actionable tiers with specific tasks.
 * Each task has time estimates, costs, and completion tracking.
 */

export interface PhaseTask {
  id: string;
  title: string;
  description: string;
  timeEstimate: string;
  costEstimate?: string;
  effort: 'quick' | 'afternoon' | 'weekend' | 'project' | 'involved';
  category: 'training' | 'financial' | 'supplies' | 'health' | 'comms' | 'documents' | 'digital' | 'home';
  seasonal?: boolean;
  refreshInterval?: string;
  keyword: string; // For dedup matching against AI actions
  domains: string[];
}

export interface TaskTier {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  whyContent: string; // Educational "why this matters" paragraph
  minPhaseToShow: number;
  conditionNote?: string;
  tasks: PhaseTask[];
}

// ============================================================================
// TIER 1: THE BASICS (Phases 0 + 1)
// ============================================================================
const TIER_BASICS: TaskTier = {
  id: 'basics',
  title: 'The Basics',
  subtitle: 'Getting your house in order',
  description: 'Every household should have this. Most of it takes an afternoon.',
  whyContent: 'The foundation everything else builds on. When these are done, your family can handle a long weekend without power, a store trip, or phone access.',
  minPhaseToShow: 0,
  tasks: [
    {
      id: 'basics-cpr',
      title: 'Take a CPR and First Aid class',
      description: 'The one skill that could save a life in 3 minutes. Red Cross or community classes available.',
      timeEstimate: '~4 hrs',
      costEstimate: '$50-80',
      effort: 'afternoon',
      category: 'training',
      keyword: 'cpr',
      domains: ['security_infrastructure'],
    },
    {
      id: 'basics-cash',
      title: 'Keep $300-500 cash at home',
      description: 'Card networks can fail during grid or banking stress. Small bills in a drawer are your backup when machines don\'t work.',
      timeEstimate: '~15 min',
      costEstimate: '$300-500',
      effort: 'quick',
      category: 'financial',
      keyword: 'cash',
      domains: ['economy'],
    },
    {
      id: 'basics-food',
      title: 'Stock 72 hours of shelf-stable food',
      description: 'Supply chains can freeze for days during crises. Stock canned goods, rice, pasta — food you actually eat.',
      timeEstimate: '~1 hr',
      costEstimate: '$75-100',
      effort: 'quick',
      category: 'supplies',
      seasonal: true,
      refreshInterval: '6 months',
      keyword: 'food',
      domains: ['supply_chain'],
    },
    {
      id: 'basics-water',
      title: 'Store 9 gallons of water',
      description: 'Taps can stop flowing during infrastructure failures. Store 1 gallon per person per day for 3 days.',
      timeEstimate: '~10 min',
      costEstimate: '$10-15',
      effort: 'quick',
      category: 'supplies',
      seasonal: true,
      refreshInterval: '12 months',
      keyword: 'water',
      domains: ['supply_chain'],
    },
    {
      id: 'basics-firstaid',
      title: 'Assemble a first aid kit',
      description: 'ERs get overwhelmed during emergencies. Basic medical supplies let you handle minor injuries at home.',
      timeEstimate: '~30 min',
      costEstimate: '$40-60',
      effort: 'quick',
      category: 'health',
      keyword: 'first aid',
      domains: ['security_infrastructure'],
    },
    {
      id: 'basics-radio',
      title: 'Get an emergency radio',
      description: 'Internet and TV go dark when power fails. A hand-crank radio keeps you informed.',
      timeEstimate: '~15 min',
      costEstimate: '$30-50',
      effort: 'quick',
      category: 'comms',
      keyword: 'radio',
      domains: ['security_infrastructure'],
    },
    {
      id: 'basics-documents',
      title: 'Organize important documents',
      description: 'If you need to leave quickly, you need ID and records in one grab. Keep passports, certificates, and insurance together.',
      timeEstimate: '~45 min',
      effort: 'afternoon',
      category: 'documents',
      keyword: 'document',
      domains: ['domestic_control'],
    },
    {
      id: 'basics-contacts',
      title: 'Write down emergency contacts',
      description: 'When phones are dead, you need numbers on paper. Write down family, doctors, and neighbors in the kitchen.',
      timeEstimate: '~20 min',
      effort: 'quick',
      category: 'comms',
      keyword: 'contact',
      domains: ['security_infrastructure'],
    },
  ],
};

// ============================================================================
// TIER 2: FINANCIALLY SECURE (Phase 2.5)
// ============================================================================
const TIER_FINANCIAL: TaskTier = {
  id: 'financially-secure',
  title: 'Financially Secure',
  subtitle: 'Your money works even when systems don\'t',
  description: 'A financial cushion that turns uncertainty into runway.',
  whyContent: 'Money is the first thing that gets disrupted — and the last thing to recover. These tasks give you 3 months of runway and options outside the banking system.',
  minPhaseToShow: 2,
  tasks: [
    {
      id: 'finance-emergency-fund',
      title: 'Build a 3-month expense cushion',
      description: 'Job loss or economic stress can hit without warning. Three months of runway in savings or T-bills gives you options.',
      timeEstimate: '~1 hr to set up',
      effort: 'involved',
      category: 'financial',
      keyword: 'emergency fund',
      domains: ['economy'],
    },
    {
      id: 'finance-non-dollar',
      title: 'Open a small non-dollar position',
      description: 'Dollar value can drop during debt or trade crises. A small position in gold or foreign currency is insurance.',
      timeEstimate: '~1 hr',
      costEstimate: '$500-1000',
      effort: 'afternoon',
      category: 'financial',
      keyword: 'non-dollar',
      domains: ['economy', 'oil_axis'],
    },
    {
      id: 'finance-go-folder',
      title: 'Build your go-folder',
      description: 'Evacuations happen fast — you need critical documents ready to grab. Physical folder with passports, insurance, and tax records.',
      timeEstimate: '~2 hrs',
      effort: 'afternoon',
      category: 'documents',
      keyword: 'go-folder',
      domains: ['domestic_control'],
    },
    {
      id: 'finance-dual-backup',
      title: 'Set up dual-jurisdiction data backup',
      description: 'Data can be locked or lost if domestic systems fail. Keep critical files in both US and international cloud storage.',
      timeEstimate: '~1 hr',
      effort: 'afternoon',
      category: 'digital',
      keyword: 'backup',
      domains: ['security_infrastructure'],
    },
    {
      id: 'finance-beneficiaries',
      title: 'Review beneficiaries and account access',
      description: 'If something happens to you, family needs immediate access. Ensure spouse is on every account with written access info.',
      timeEstimate: '~1 hr',
      effort: 'afternoon',
      category: 'financial',
      keyword: 'beneficiary',
      domains: ['economy'],
    },
  ],
};

// ============================================================================
// TIER 3: CONNECTED & PROTECTED (Phases 2 + 3)
// ============================================================================
const TIER_CONNECTED: TaskTier = {
  id: 'connected-protected',
  title: 'Connected & Protected',
  subtitle: 'Comms, health, and digital resilience',
  description: 'If internet goes down or air quality tanks, your family stays connected and breathing clean.',
  whyContent: 'When the internet goes down or the air quality tanks, your family stays connected and breathing clean air. These are the systems that work when normal ones don\'t.',
  minPhaseToShow: 2,
  tasks: [
    {
      id: 'connected-passwords',
      title: 'Lock down your digital life',
      description: 'Account breaches spike during chaotic periods. Password manager + 2FA protects your money and identity.',
      timeEstimate: '~2 hrs',
      effort: 'afternoon',
      category: 'digital',
      keyword: '2fa',
      domains: ['security_infrastructure'],
    },
    {
      id: 'connected-backup',
      title: 'Set up encrypted cloud backup',
      description: 'Devices get lost, stolen, or destroyed — your data shouldn\'t. Cloud backup means recovery in 30 minutes.',
      timeEstimate: '~1 hr',
      effort: 'afternoon',
      category: 'digital',
      keyword: 'backup',
      domains: ['security_infrastructure'],
    },
    {
      id: 'connected-powerbanks',
      title: 'Get two 20,000mAh power banks',
      description: 'Keeps phones alive for 4-5 days without grid power. Charge monthly.',
      timeEstimate: '~5 min to order',
      costEstimate: '$40-60',
      effort: 'quick',
      category: 'supplies',
      keyword: 'power bank',
      domains: ['energy'],
    },
    {
      id: 'connected-radios',
      title: 'Get GMRS radios for the family',
      description: 'When cell networks jam, you can still reach each other. Program family and neighbor channels.',
      timeEstimate: '~30 min to set up',
      costEstimate: '$80-120',
      effort: 'quick',
      category: 'comms',
      keyword: 'radio',
      domains: ['security_infrastructure'],
    },
    {
      id: 'connected-offline-phone',
      title: 'Keep an offline phone in a Faraday pouch',
      description: 'Main phones can be tracked, hacked, or bricked remotely. A backup phone in signal-blocking pouch stays clean.',
      timeEstimate: '~30 min to set up',
      costEstimate: '$50-80',
      effort: 'quick',
      category: 'comms',
      keyword: 'faraday',
      domains: ['security_infrastructure'],
    },
    {
      id: 'connected-rx',
      title: 'Get 90-day buffer on prescriptions',
      description: 'Pharmacy supply chains can break during strikes or shortages. A 90-day buffer means you\'re not scrambling.',
      timeEstimate: '~15 min phone call',
      effort: 'quick',
      category: 'health',
      keyword: 'prescription',
      domains: ['supply_chain'],
    },
    {
      id: 'connected-n95',
      title: 'Stock 20 N95 masks per person',
      description: 'Air quality can crash from wildfires, bio events, or industrial accidents. N95s let you breathe safely.',
      timeEstimate: '~5 min to order',
      costEstimate: '$15-25',
      effort: 'quick',
      category: 'health',
      seasonal: true,
      refreshInterval: '24 months',
      keyword: 'n95',
      domains: ['security_infrastructure'],
    },
    {
      id: 'connected-hepa',
      title: 'Build a Corsi-Rosenthal box',
      description: 'Indoor air turns dangerous during wildfires or chemical events. A DIY air filter cleans a room for $60.',
      timeEstimate: '~30 min to build',
      costEstimate: '$60',
      effort: 'quick',
      category: 'health',
      keyword: 'hepa',
      domains: ['security_infrastructure'],
    },
    {
      id: 'connected-seal-kit',
      title: 'Assemble a room seal kit',
      description: 'Chemical spills or attacks require sealing a room fast. Pre-cut plastic and tape means 5-minute protection.',
      timeEstimate: '~30 min to prep',
      costEstimate: '$20',
      effort: 'quick',
      category: 'health',
      keyword: 'seal',
      domains: ['security_infrastructure'],
    },
  ],
};

// ============================================================================
// TIER 4: STORAGE & SHELTER (Phases 4 + 6)
// ============================================================================
const TIER_STORAGE: TaskTier = {
  id: 'storage',
  title: 'Storage & Shelter',
  subtitle: 'Creating your supply hub',
  description: 'A clean, dry, organized space for supplies and shelter-in-place. Basement, garage, or large closet.',
  whyContent: 'Turning unused space into organized storage and shelter. Whether it\'s a basement, garage, or spare room — this becomes your supply hub when you need it most.',
  minPhaseToShow: 4,
  conditionNote: 'Current conditions suggest setting up dedicated storage. Do these in order.',
  tasks: [
    {
      id: 'storage-assess',
      title: 'Pick and assess your storage space',
      description: 'Supplies need a home that won\'t ruin them. Check your basement, garage, or closet for moisture, pests, and temperature.',
      timeEstimate: '~30 min',
      effort: 'quick',
      category: 'home',
      keyword: 'assess',
      domains: ['security_infrastructure'],
    },
    {
      id: 'storage-climate',
      title: 'Address climate control',
      description: 'Temperature swings and humidity destroy food and supplies. A dehumidifier and insulation protect your investment.',
      timeEstimate: '~2-3 hrs',
      costEstimate: '$50-200',
      effort: 'afternoon',
      category: 'home',
      keyword: 'climate',
      domains: ['security_infrastructure'],
    },
    {
      id: 'storage-sensors',
      title: 'Install leak sensors and CO detector',
      description: 'Water damage and CO poisoning can happen while you\'re away. Sensors give you early warning on your phone.',
      timeEstimate: '~30 min',
      costEstimate: '$80',
      effort: 'quick',
      category: 'home',
      keyword: 'sensor',
      domains: ['security_infrastructure'],
    },
    {
      id: 'storage-cleanout',
      title: 'Clear and clean the space',
      description: 'You can\'t build a supply hub in a cluttered space. Clear the room so organization is possible.',
      timeEstimate: 'A full weekend',
      costEstimate: '$50-100',
      effort: 'weekend',
      category: 'home',
      keyword: 'cleanout',
      domains: ['security_infrastructure'],
    },
    {
      id: 'storage-shelving',
      title: 'Set up shelving and supply bins',
      description: 'In a crisis you need to find things fast. Labeled bins on sturdy shelves mean no frantic searching.',
      timeEstimate: '~3-4 hrs',
      costEstimate: '$200-300',
      effort: 'afternoon',
      category: 'home',
      keyword: 'shelving',
      domains: ['supply_chain'],
    },
    {
      id: 'storage-lighting',
      title: 'Add lighting and a radio',
      description: 'Shelter space is useless if you can\'t see or get information. Battery lights and radio keep you functional.',
      timeEstimate: '~30 min',
      costEstimate: '$60-80',
      effort: 'quick',
      category: 'supplies',
      keyword: 'lighting',
      domains: ['security_infrastructure'],
    },
    {
      id: 'storage-inventory',
      title: 'Create a supply inventory',
      description: 'Expired food and forgotten supplies are useless. A simple inventory tells you what\'s ready and what needs restocking.',
      timeEstimate: '~1 hr',
      effort: 'quick',
      category: 'documents',
      keyword: 'inventory',
      domains: ['supply_chain'],
    },
  ],
};

// ============================================================================
// TIER 5: ENERGY INDEPENDENCE (Phases 5 + 7)
// ============================================================================
const TIER_ENERGY: TaskTier = {
  id: 'energy-independence',
  title: 'Energy Independence',
  subtitle: 'Your house runs when the grid doesn\'t',
  description: 'Turn your oil tank from heating system into complete backup power infrastructure.',
  whyContent: 'Your oil tank becomes complete backup power infrastructure. When the grid goes down, your family keeps the lights on, the fridge running, and the heat flowing.',
  minPhaseToShow: 5,
  conditionNote: 'Energy and conflict indicators suggest accelerating power independence.',
  tasks: [
    {
      id: 'energy-fuel-sample',
      title: 'Get fuel sampled',
      description: 'Contaminated fuel can destroy your burner or generator when you need it most. A test catches problems early.',
      timeEstimate: '~1 hr (tech visit)',
      costEstimate: '$50-100',
      effort: 'quick',
      category: 'home',
      keyword: 'fuel sample',
      domains: ['energy', 'oil_axis'],
    },
    {
      id: 'energy-biocide',
      title: 'Add stabilizer and biocide',
      description: 'Fuel degrades and grows bacteria over time. Stabilizer and biocide keep your tank healthy for years.',
      timeEstimate: '~15 min',
      costEstimate: '$30-50',
      effort: 'quick',
      category: 'home',
      keyword: 'biocide',
      domains: ['energy'],
    },
    {
      id: 'energy-racor-filter',
      title: 'Install a Racor fuel filter',
      description: 'Water and sludge in fuel lines cause equipment failure. A filter catches contaminants before they do damage.',
      timeEstimate: '~2 hrs',
      costEstimate: '$80-120',
      effort: 'afternoon',
      category: 'home',
      keyword: 'racor',
      domains: ['energy'],
    },
    {
      id: 'energy-fuel-strategy',
      title: 'Decide: direct draw vs day tank',
      description: 'Your generator needs fuel access you can manage safely. Direct draw is simpler; a day tank is safer.',
      timeEstimate: '~30 min research',
      effort: 'quick',
      category: 'home',
      keyword: 'day tank',
      domains: ['energy'],
    },
    {
      id: 'energy-assessment',
      title: 'Get electrician assessment',
      description: 'Generator installation requires proper sizing and panel work. An electrician assessment prevents costly mistakes.',
      timeEstimate: 'One afternoon',
      costEstimate: '$200',
      effort: 'afternoon',
      category: 'home',
      keyword: 'electrician',
      domains: ['energy'],
    },
    {
      id: 'energy-generator-install',
      title: 'Install standby generator',
      description: 'Extended outages can last weeks — your family needs power that doesn\'t depend on the grid. A diesel genset auto-starts when power fails.',
      timeEstimate: '2-3 days (professional)',
      costEstimate: '$8,000-12,000',
      effort: 'project',
      category: 'home',
      keyword: 'generator',
      domains: ['energy'],
    },
    {
      id: 'energy-shelter-circuits',
      title: 'Wire basement to generator',
      description: 'Your shelter space needs power during outages. Wiring it to the generator keeps lights and dehumidifier running.',
      timeEstimate: 'Part of install',
      effort: 'quick',
      category: 'home',
      keyword: 'circuit',
      domains: ['energy', 'security_infrastructure'],
    },
  ],
};

// ============================================================================
// TIER 6: WATER & BEYOND (Phases 8 + 9)
// ============================================================================
const TIER_ADVANCED: TaskTier = {
  id: 'advanced',
  title: 'Water & Beyond',
  subtitle: 'Advanced resilience infrastructure',
  description: 'Significant projects. Most families never go this far — and that\'s fine.',
  whyContent: 'Long-term investments that only surface when conditions warrant. These are serious projects — but if you\'re seeing this section, conditions suggest they\'re worth considering.',
  minPhaseToShow: 7,
  conditionNote: 'Multiple indicators suggest investing in long-term infrastructure.',
  tasks: [
    {
      id: 'adv-rainwater',
      title: 'Install rainwater collection',
      description: 'Municipal water can fail for extended periods. Rainwater collection gives you renewable water independence.',
      timeEstimate: 'Multiple weekends',
      costEstimate: '$2,000-3,000',
      effort: 'project',
      category: 'home',
      keyword: 'rainwater',
      domains: ['supply_chain'],
    },
    {
      id: 'adv-indoor-filter',
      title: 'Set up indoor water filtration',
      description: 'Water quality can degrade or become contaminated during emergencies. Gravity filter + UV turns any water drinkable.',
      timeEstimate: '~2 hrs',
      costEstimate: '$300-500',
      effort: 'afternoon',
      category: 'home',
      keyword: 'filter',
      domains: ['supply_chain'],
    },
    {
      id: 'adv-saferoom',
      title: 'Assess safe room options',
      description: 'Severe weather and security threats need a hardened space. An engineer can assess FEMA-standard safe room options.',
      timeEstimate: 'Assessment first',
      costEstimate: '$5,000-15,000',
      effort: 'project',
      category: 'home',
      keyword: 'safe room',
      domains: ['security_infrastructure', 'global_conflict'],
    },
  ],
};

// ============================================================================
// M-PHASE TIERS (Migration/Relocation - triggered by domestic control)
// ============================================================================

export interface MPhaseTask {
  id: string;
  title: string;
  description: string;
  timeEstimate: string;
  costEstimate?: string;
  effort: 'quick' | 'afternoon' | 'weekend' | 'project' | 'involved';
  category: 'documents' | 'research' | 'logistics' | 'financial';
  keyword: string;
}

export interface MPhaseTier {
  level: 0 | 1 | 2;
  title: string;
  subtitle: string;
  description: string;
  whyContent: string;
  tasks: MPhaseTask[];
}

const M_PHASE_0: MPhaseTier = {
  level: 0,
  title: 'Document Review',
  subtitle: 'Passport and vital document readiness',
  description: 'Ensure your core travel and identity documents are current and accessible.',
  whyContent: 'When domestic conditions shift, having current documents means options remain open. These tasks take minimal time but provide maximum flexibility.',
  tasks: [
    {
      id: 'm0-passport-verify',
      title: 'Verify passport expiration dates',
      description: 'Many countries require 6+ months validity. Check all family passports and note renewal deadlines.',
      timeEstimate: '~10 min',
      effort: 'quick',
      category: 'documents',
      keyword: 'passport',
    },
    {
      id: 'm0-vital-docs',
      title: 'Gather vital documents in go-folder',
      description: 'Birth certificates, marriage license, professional credentials, medical records. Keep originals + digital copies.',
      timeEstimate: '~2 hrs',
      effort: 'afternoon',
      category: 'documents',
      keyword: 'vital documents',
    },
    {
      id: 'm0-overseas-assets',
      title: 'Review overseas assets and accounts',
      description: 'Inventory any foreign bank accounts, property, or investments. Ensure access credentials are current.',
      timeEstimate: '~1 hr',
      effort: 'afternoon',
      category: 'financial',
      keyword: 'overseas',
    },
    {
      id: 'm0-apostille',
      title: 'Get apostilles for key documents',
      description: 'Apostille authentication lets documents be recognized abroad. Birth certificates and degrees are priorities.',
      timeEstimate: '~2-4 weeks',
      costEstimate: '$50-100',
      effort: 'involved',
      category: 'documents',
      keyword: 'apostille',
    },
  ],
};

const M_PHASE_1: MPhaseTier = {
  level: 1,
  title: 'Visa Research',
  subtitle: 'Exploring relocation options',
  description: 'Research visa pathways and begin preliminary planning for potential relocation.',
  whyContent: 'Sustained pressure on domestic freedoms warrants understanding your options. Research now means faster action if needed later.',
  tasks: [
    {
      id: 'm1-visa-research',
      title: 'Research visa requirements for target countries',
      description: 'Identify 2-3 potential destinations. Research work permits, residency requirements, and timeline.',
      timeEstimate: '~4-6 hrs',
      effort: 'afternoon',
      category: 'research',
      keyword: 'visa',
    },
    {
      id: 'm1-immigration-attorney',
      title: 'Contact immigration attorney',
      description: 'A 30-minute consultation can clarify your best options. Get recommendations for your profession and family situation.',
      timeEstimate: '~1 hr',
      costEstimate: '$200-400',
      effort: 'afternoon',
      category: 'research',
      keyword: 'immigration',
    },
    {
      id: 'm1-asset-portability',
      title: 'Evaluate property and asset portability',
      description: 'Understand tax implications of moving assets abroad. Review real estate, retirement accounts, and business interests.',
      timeEstimate: '~2-3 hrs',
      effort: 'afternoon',
      category: 'financial',
      keyword: 'asset portability',
    },
    {
      id: 'm1-remote-work',
      title: 'Assess remote work viability',
      description: 'Can your job go remote or international? Research digital nomad visas and employer policies.',
      timeEstimate: '~1 hr',
      effort: 'quick',
      category: 'research',
      keyword: 'remote work',
    },
    {
      id: 'm1-language',
      title: 'Begin language preparation',
      description: 'If target countries require another language, start basics. Even A1 level helps with daily life.',
      timeEstimate: 'Ongoing',
      costEstimate: '$0-200',
      effort: 'project',
      category: 'research',
      keyword: 'language',
    },
  ],
};

const M_PHASE_2: MPhaseTier = {
  level: 2,
  title: 'Trial Relocation',
  subtitle: 'Testing relocation logistics',
  description: 'Execute a trial stay to test the practical realities of relocation.',
  whyContent: 'Sustained high-risk domestic conditions suggest testing your exit plan. A trial stay reveals what works and what needs adjustment.',
  tasks: [
    {
      id: 'm2-trial-stay',
      title: 'Book 2-4 week trial stay in target location',
      description: 'Rent an apartment, not a hotel. Live as a resident to test daily logistics.',
      timeEstimate: '~2 hrs to book',
      costEstimate: '$2,000-5,000',
      effort: 'afternoon',
      category: 'logistics',
      keyword: 'trial stay',
    },
    {
      id: 'm2-banking',
      title: 'Test banking and financial access',
      description: 'Open local bank account if possible. Test ATM access, wire transfers, and card acceptance.',
      timeEstimate: '~3 hrs',
      effort: 'afternoon',
      category: 'financial',
      keyword: 'banking',
    },
    {
      id: 'm2-communication',
      title: 'Establish communication setup',
      description: 'Get local SIM, test VPN, verify work communication tools function. Set up local phone number.',
      timeEstimate: '~2 hrs',
      effort: 'afternoon',
      category: 'logistics',
      keyword: 'communication',
    },
    {
      id: 'm2-local-contacts',
      title: 'Establish local contacts',
      description: 'Connect with expat communities, local professionals, and potential employers. LinkedIn and local meetups help.',
      timeEstimate: '~4-6 hrs',
      effort: 'weekend',
      category: 'logistics',
      keyword: 'contacts',
    },
    {
      id: 'm2-schools',
      title: 'Research schools and childcare',
      description: 'If you have children, visit schools during your trial stay. Understand enrollment timelines.',
      timeEstimate: '~4 hrs',
      effort: 'afternoon',
      category: 'research',
      keyword: 'schools',
    },
    {
      id: 'm2-healthcare',
      title: 'Assess healthcare access',
      description: 'Visit a clinic, understand insurance requirements, locate specialists for any ongoing needs.',
      timeEstimate: '~2 hrs',
      effort: 'afternoon',
      category: 'logistics',
      keyword: 'healthcare',
    },
  ],
};

export const M_PHASE_TIERS: MPhaseTier[] = [M_PHASE_0, M_PHASE_1, M_PHASE_2];

export function getMPhaseTier(level: 0 | 1 | 2): MPhaseTier {
  return M_PHASE_TIERS[level];
}

export function getMPhaseProgress(level: 0 | 1 | 2, completedTaskIds: Set<string>): {
  completed: number;
  total: number;
  percentage: number;
} {
  const tier = getMPhaseTier(level);
  const completed = tier.tasks.filter(t => completedTaskIds.has(t.id)).length;
  const total = tier.tasks.length;
  return {
    completed,
    total,
    percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
  };
}

// ============================================================================
// EXPORTS
// ============================================================================

export const TASK_TIERS: TaskTier[] = [
  TIER_BASICS,
  TIER_FINANCIAL,
  TIER_CONNECTED,
  TIER_STORAGE,
  TIER_ENERGY,
  TIER_ADVANCED,
];

export function getTierById(tierId: string): TaskTier | undefined {
  return TASK_TIERS.find(t => t.id === tierId);
}

export function getTaskById(taskId: string): PhaseTask | undefined {
  for (const tier of TASK_TIERS) {
    const task = tier.tasks.find(t => t.id === taskId);
    if (task) return task;
  }
  return undefined;
}

export function getVisibleTiers(systemPhase: number | 'tighten-up'): TaskTier[] {
  const phase = systemPhase === 'tighten-up' ? 7 : systemPhase;
  return TASK_TIERS.filter(tier => tier.minPhaseToShow <= phase);
}

export function getTasksForPhase(systemPhase: number): PhaseTask[] {
  const tiers = getVisibleTiers(systemPhase);
  return tiers.flatMap(tier => tier.tasks);
}

export function computeReadinessFromTiers(
  completedTaskIds: Set<string>
): { effectivePhase: number; description: string } {
  const isTierComplete = (tier: TaskTier) =>
    tier.tasks.every(t => completedTaskIds.has(t.id));

  const basicsComplete = isTierComplete(TIER_BASICS);
  const financeComplete = isTierComplete(TIER_FINANCIAL);
  const connectedComplete = isTierComplete(TIER_CONNECTED);
  const storageComplete = isTierComplete(TIER_STORAGE);
  const energyComplete = isTierComplete(TIER_ENERGY);
  const advancedComplete = isTierComplete(TIER_ADVANCED);

  if (advancedComplete) return { effectivePhase: 9, description: 'Fully resilient' };
  if (energyComplete) return { effectivePhase: 7, description: 'Energy independent' };
  if (storageComplete) return { effectivePhase: 6, description: 'Shelter ready' };
  if (connectedComplete) return { effectivePhase: 3, description: 'Connected and protected' };
  if (financeComplete) return { effectivePhase: 2.5, description: 'Financially buffered' };
  if (basicsComplete) return { effectivePhase: 1, description: 'Basics covered' };
  return { effectivePhase: 0, description: 'Getting started' };
}

export function getTierProgress(tier: TaskTier, completedTaskIds: Set<string>): {
  completed: number;
  total: number;
  percentage: number;
} {
  const completed = tier.tasks.filter(t => completedTaskIds.has(t.id)).length;
  const total = tier.tasks.length;
  return {
    completed,
    total,
    percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
  };
}

// Get the phase description for display
export function getPhaseDescription(phase: number): string {
  const descriptions: Record<number, string> = {
    0: '72-hour basics',
    1: 'Essential preparedness',
    2: 'Digital and financial buffer',
    3: 'Comms and health resilience',
    4: 'Shelter preparation',
    5: 'Energy infrastructure',
    6: 'Shelter completion',
    7: 'Power independence',
    8: 'Water independence',
    9: 'Full resilience',
  };
  return descriptions[phase] || 'Unknown phase';
}
