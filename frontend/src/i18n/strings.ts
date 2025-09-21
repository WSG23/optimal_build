export type Locale = 'en' | 'zh'

export interface AppStrings {
  app: {
    title: string
    tagline: string
    helper: string
  }
  nav: {
    home: string
    upload: string
    detection: string
    pipelines: string
    feasibility: string
  }
  uploader: {
    title: string
    subtitle: string
    dropHint: string
    browseLabel: string
    latestStatus: string
    parsing: string
    ready: string
    error: string
    overlays: string
    hints: string
    zone: string
  }
  detection: {
    title: string
    subtitle: string
    overlays: string
    advisory: string
    tableHeading: string
    unit: string
    floor: string
    area: string
    status: string
    empty: string
    locked: string
    exportCta: string
  }
  pipelines: {
    title: string
    subtitle: string
    suggestionHeading: string
    pipelineFocus: string
    automationScore: string
    reviewHours: string
    savings: string
  }
  controls: {
    source: string
    pending: string
    approved: string
    rejected: string
    showLayer: string
    hideLayer: string
    approveAll: string
    rejectAll: string
    lockZone: string
    unlockZone: string
    locked: string
  }
  panels: {
    rulePackTitle: string
    rulePackEmpty: string
    auditTitle: string
    exportTitle: string
    exportSubtitle: string
    roiTitle: string
    roiSubtitle: string
  }
}

export const STRINGS: Record<Locale, AppStrings> = {
  en: {
    app: {
      title: 'Optimal Build Studio',
      tagline: 'Accelerate compliance and design coordination across your CAD workflows.',
      helper: 'Switch language',
    },
    nav: {
      home: 'Overview',
      upload: 'Upload CAD',
      detection: 'Floor & unit detection',
      pipelines: 'Default pipelines',
      feasibility: 'Feasibility wizard',
    },
    uploader: {
      title: 'Upload building layouts',
      subtitle: 'Drop DXF/DWG files to launch the parse pipeline and monitor overlays in real-time.',
      dropHint: 'Drag & drop or paste files here',
      browseLabel: 'Browse files',
      latestStatus: 'Latest status',
      parsing: 'Processing CAD layers…',
      ready: 'Parse completed',
      error: 'Something went wrong while parsing the CAD file.',
      overlays: 'Detected overlays',
      hints: 'Authority hints',
      zone: 'Zone',
    },
    detection: {
      title: 'Floor and unit detection preview',
      subtitle: 'Review detected spaces, approve batches and understand overlay impact.',
      overlays: 'Overlays in effect',
      advisory: 'Authority advisory hints',
      tableHeading: 'Detected units',
      unit: 'Unit',
      floor: 'Floor',
      area: 'Area (sqm)',
      status: 'Status',
      empty: 'No units match the current filters.',
      locked: 'Zone is locked. Unlock to update review status.',
      exportCta: 'Export review pack',
    },
    pipelines: {
      title: 'Default pipeline suggestions',
      subtitle: 'Leverage rule packs tailored to the detected overlays and topics.',
      suggestionHeading: 'Suggested automation pipelines',
      pipelineFocus: 'Focus',
      automationScore: 'Automation score',
      reviewHours: 'Manual review hours saved',
      savings: 'Estimated compliance savings',
    },
    controls: {
      source: 'Source',
      pending: 'Pending',
      approved: 'Approved',
      rejected: 'Rejected',
      showLayer: 'Show layer',
      hideLayer: 'Hide layer',
      approveAll: 'Approve all pending',
      rejectAll: 'Reject all pending',
      lockZone: 'Lock zone',
      unlockZone: 'Unlock zone',
      locked: 'Zone locked',
    },
    panels: {
      rulePackTitle: 'Rule pack explanation',
      rulePackEmpty: 'Rules will appear after the first overlays are processed.',
      auditTitle: 'Audit timeline',
      exportTitle: 'Export options',
      exportSubtitle: 'Deliver CAD overlays and compliance notes in preferred formats.',
      roiTitle: 'ROI snapshot',
      roiSubtitle: 'Quantify effort saved through automation.',
    },
  },
  zh: {
    app: {
      title: 'Optimal Build Studio',
      tagline: '加速 CAD 工作流程中的合规与协同。',
      helper: '切换语言',
    },
    nav: {
      home: '概览',
      upload: '上传 CAD',
      detection: '楼层与单元检测',
      pipelines: '默认流程',
      feasibility: '可行性向导',
    },
    uploader: {
      title: '上传建筑平面',
      subtitle: '拖入 DXF/DWG 文件启动解析流程并实时查看覆盖层。',
      dropHint: '拖拽或粘贴文件到此',
      browseLabel: '选择文件',
      latestStatus: '最新状态',
      parsing: '正在处理 CAD 图层…',
      ready: '解析完成',
      error: '解析 CAD 文件时出错。',
      overlays: '检测到的覆盖层',
      hints: '主管机构提示',
      zone: '分区',
    },
    detection: {
      title: '楼层与单元检测预览',
      subtitle: '审阅检测出的空间，批量审批并了解覆盖层影响。',
      overlays: '适用覆盖层',
      advisory: '主管机构提示',
      tableHeading: '检测到的单元',
      unit: '单元',
      floor: '楼层',
      area: '面积 (平方米)',
      status: '状态',
      empty: '当前筛选条件下没有单元。',
      locked: '分区已锁定，解锁后才能更新状态。',
      exportCta: '导出审查包',
    },
    pipelines: {
      title: '默认流程建议',
      subtitle: '根据检测到的覆盖层与主题推荐规则包。',
      suggestionHeading: '自动化流程建议',
      pipelineFocus: '关注点',
      automationScore: '自动化评分',
      reviewHours: '节省的人工审核时长',
      savings: '预计合规节省',
    },
    controls: {
      source: '原始',
      pending: '待处理',
      approved: '已通过',
      rejected: '已拒绝',
      showLayer: '显示图层',
      hideLayer: '隐藏图层',
      approveAll: '批量通过',
      rejectAll: '批量拒绝',
      lockZone: '锁定分区',
      unlockZone: '解锁分区',
      locked: '已锁定',
    },
    panels: {
      rulePackTitle: '规则包说明',
      rulePackEmpty: '解析完成后将显示规则列表。',
      auditTitle: '审计时间线',
      exportTitle: '导出选项',
      exportSubtitle: '以首选格式导出覆盖层与合规备注。',
      roiTitle: '投资回报速览',
      roiSubtitle: '量化自动化节省的工作量。',
    },
  },
}
