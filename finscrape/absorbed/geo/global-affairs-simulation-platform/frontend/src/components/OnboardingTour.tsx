import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

const ONBOARDING_KEY = 'ir_platform_onboarded'

const STEPS_ZH = [
  { target: 'body', placement: 'center', title: '欢迎使用国关推演平台', content: '这是一个国际关系情报分析与推演系统。接下来将为您快速介绍核心功能。' },
  { target: 'nav a[href="/pipeline"]', title: '运行分析', content: '点击"运行分析"启动完整流水线：新闻采集 → 聚类 → 事件抽象 → 理论分析 → 推演生成。' },
  { target: 'nav a[href="/events"]', title: '事件浏览', content: '查看系统抽象出的国际关系事件，包含行为主体、危机阶段、置信度等详细信息。' },
  { target: 'nav a[href="/analogies"]', title: '历史类比', content: '利用 Claude AI 从 28 个历史案例中寻找结构性类比，为当前事件提供历史参考。' },
  { target: 'nav a[href="/"]', title: '地球视图', content: '3D 地球可视化展示全球事件分布和关联关系，支持交互式探索。' },
  { target: 'nav a[href="/calibration"]', title: '预测校准', content: '追踪推演预测的准确性，通过 Brier 分数和命中率评估系统表现。' },
]

const STEPS_EN = [
  { target: 'body', placement: 'center', title: 'Welcome to IR Intel Platform', content: 'An international relations intelligence analysis and simulation system. Here is a quick tour of core features.' },
  { target: 'nav a[href="/pipeline"]', title: 'Pipeline', content: 'Run the full analysis pipeline: News Ingestion → Clustering → Event Abstraction → Theory Analysis → Scenario Generation.' },
  { target: 'nav a[href="/events"]', title: 'Events', content: 'Browse abstracted IR events with key actors, crisis stages, and confidence scores.' },
  { target: 'nav a[href="/analogies"]', title: 'Analogies', content: 'Use Claude AI to find structural analogies from 28 historical cases.' },
  { target: 'nav a[href="/"]', title: 'Globe View', content: '3D globe visualization of global event distribution and relationships.' },
  { target: 'nav a[href="/calibration"]', title: 'Calibration', content: 'Track prediction accuracy with Brier scores and hit rates.' },
]

export default function OnboardingTour() {
  const { i18n } = useTranslation()
  const [run, setRun] = useState(false)
  const [JoyrideComp, setJoyrideComp] = useState<any>(null)

  useEffect(() => {
    const done = localStorage.getItem(ONBOARDING_KEY)
    if (!done) {
      import('react-joyride').then(mod => {
        setJoyrideComp(() => mod.Joyride)
        const timer = setTimeout(() => setRun(true), 1500)
        return () => clearTimeout(timer)
      })
    }
  }, [])

  const steps = i18n.language === 'zh' ? STEPS_ZH : STEPS_EN

  const handleCallback = useCallback((data: any) => {
    const { action, status } = data
    if (
      action === 'reset' || action === 'close' || action === 'skip' ||
      status === 'finished' || status === 'skipped'
    ) {
      setRun(false)
      localStorage.setItem(ONBOARDING_KEY, '1')
    }
  }, [])

  if (!run || !JoyrideComp) return null

  return (
    <JoyrideComp
      steps={steps}
      run={run}
      callback={handleCallback}
      continuous
      showProgress
      showSkipButton
      styles={{
        options: {
          primaryColor: '#3b5bdb',
          zIndex: 10000,
        },
      }}
      locale={{
        back: i18n.language === 'zh' ? '上一步' : 'Back',
        next: i18n.language === 'zh' ? '下一步' : 'Next',
        skip: i18n.language === 'zh' ? '跳过' : 'Skip',
        last: i18n.language === 'zh' ? '完成' : 'Done',
      }}
    />
  )
}
