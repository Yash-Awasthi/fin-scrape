// Professional messaging for Canairy
export const canairyMessages = {
  // Brand messaging
  brand: {
    tagline: "Household Resilience Monitoring",
    subtitle: "Early warning. Informed action. Peace of mind.",
    description: "Canairy monitors critical indicators and provides actionable preparedness guidance.",
  },

  // Status messages
  status: {
    allGood: {
      title: "All Clear",
      message: "All indicators are within normal range. Continue standard monitoring.",
      icon: "check",
    },
    attention: {
      title: "Elevated Alert",
      message: "Some indicators require attention. Review status and consider preparedness actions.",
      icon: "alert",
    },
    action: {
      title: "Action Required",
      message: "Multiple indicators are elevated. Activate preparedness protocols.",
      icon: "warning",
    },
  },

  // Indicator labels
  indicators: {
    MarketVolatility: {
      old: "Market volatility spike",
      new: "Market Volatility Index",
      description: "Measures intraday market stress and systemic risk signals",
    },
    TreasuryYield: {
      old: "Treasury yield inversion",
      new: "Treasury Auction Stress",
      description: "Bond market demand and liquidity indicators",
    },
    JoblessClaims: {
      old: "Jobless claims surge",
      new: "Unemployment Claims",
      description: "Weekly jobless claims and labor market stress",
    },
    GroceryCPI: {
      old: "Food inflation spike",
      new: "Food Price Index",
      description: "Consumer food price inflation rate",
    },
    GDPGrowth: {
      old: "GDP contraction",
      new: "Economic Growth",
      description: "Real GDP quarter-over-quarter change",
    },
    GlobalConflict: {
      old: "Global conflict intensity",
      new: "Global Conflict Index",
      description: "Worldwide armed conflict intensity",
    },
    TaiwanPLA: {
      old: "Taiwan Strait tensions",
      new: "Taiwan Strait Activity",
      description: "PLA military activity near Taiwan ADIZ",
    },
    NATOReadiness: {
      old: "NATO readiness level",
      new: "NATO Alert Status",
      description: "Alliance high-readiness force activations",
    },
    NuclearTests: {
      old: "Nuclear test activity",
      new: "Nuclear/ICBM Activity",
      description: "Nuclear detonation and missile test events",
    },
    GridOutage: {
      old: "Grid outage frequency",
      new: "Grid Reliability",
      description: "Major power outage incidents",
    },
    CISACyber: {
      old: "Cyber attack frequency",
      new: "Cyber Threat Level",
      description: "Critical infrastructure vulnerability alerts",
    },
    WHODisease: {
      old: "Novel disease H2H transmission",
      new: "Pandemic Risk",
      description: "Novel pathogen human-to-human transmission",
    },
    StrikeTracker: {
      old: "Labor strike activity",
      new: "Labor Disruption",
      description: "Strike activity and worker-days lost",
    },
    SchoolClosures: {
      old: "School closure rate",
      new: "School Operations",
      description: "Educational facility closure rate",
    },
    PharmacyShortage: {
      old: "Pharmacy shortage reports",
      new: "Medical Supply Status",
      description: "Critical medication availability",
    },
  },

  // Action messages by alert level
  actions: {
    green: {
      title: "Maintain Readiness",
      items: [
        "Review emergency contact list",
        "Verify emergency supplies are current",
        "Confirm family communication plan",
        "Check expiration dates on stored items",
      ],
    },
    amber: {
      title: "Increase Preparedness",
      items: [
        "Keep vehicle fuel above half tank",
        "Stock 2 weeks of essential supplies",
        "Verify cash reserves are accessible",
        "Confirm communication plan with family",
        "Review evacuation routes",
      ],
    },
    red: {
      title: "Activate Protocols",
      items: [
        "Fill all vehicles to capacity",
        "Complete 30-day supply stockpile",
        "Withdraw emergency cash reserves",
        "Charge all devices and backup batteries",
        "Confirm rally points with family members",
        "Review and execute preparedness checklist",
      ],
    },
  },

  // Onboarding
  onboarding: {
    welcome: {
      title: "Welcome to Canairy",
      steps: [
        "Configure monitoring preferences",
        "Set alert thresholds",
        "Add household members",
        "Review preparedness checklist",
        "Enable notifications",
      ],
    },
  },

  // Milestones
  achievements: {
    firstWeek: {
      title: "Active Monitoring",
      description: "7 days of continuous monitoring",
    },
    allGreen: {
      title: "All Clear Status",
      description: "All indicators within normal range",
    },
    actionComplete: {
      title: "Protocol Complete",
      description: "Completed preparedness checklist",
    },
    neighborHelp: {
      title: "Community Resilience",
      description: "Extended preparedness network",
    },
  },

  // Help text
  help: {
    whatIsThis: "Canairy aggregates data from government, financial, and security sources to provide early warning of systemic risks affecting household resilience.",
    howItWorks: "Indicators are updated continuously from authoritative sources. Alert levels are calculated based on predefined thresholds calibrated to historical risk events.",
    whyPrepare: "Preparedness reduces response time and increases options during disruptions. Small actions now compound into significant resilience.",
  },
};
