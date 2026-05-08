import { useMemo } from 'react'
import { useTranslation } from '../i18n'
import { useDeveloperMode } from '../contexts/useDeveloperMode'
import { useOptionalProject } from '../contexts/useProject'

export type NavGroup = {
  title?: string
  items: Array<{ path: string; label: string; description?: string }>
}

export function useNavGroups(): NavGroup[] {
  const { t } = useTranslation()
  const { isDeveloperMode } = useDeveloperMode()
  const projectContext = useOptionalProject()
  const currentProject = projectContext?.currentProject ?? null

  const projectBase = currentProject?.id
    ? `/projects/${currentProject.id}`
    : null

  return useMemo(() => {
    const groups: NavGroup[] = [
      {
        title: 'Analysis',
        items: [
          {
            path: '/visualizations/intelligence',
            label: t('nav.intelligence'),
            description: 'Market intelligence and insights',
          },
          {
            path: projectBase ? `${projectBase}/feasibility` : '/projects',
            label: t('nav.feasibility'),
            description: 'Development feasibility analysis',
          },
          {
            path: projectBase ? `${projectBase}/finance` : '/projects',
            label: t('nav.finance'),
            description: 'Financial modeling and scenarios',
          },
        ],
      },
      {
        title: 'Field',
        items: [
          {
            path: '/app/capture',
            label: t('nav.capture'),
            description: 'GPS site capture and observations',
          },
        ],
      },
    ]

    if (isDeveloperMode) {
      groups.push(
        {
          title: 'Execution',
          items: [
            {
              path: projectBase
                ? `${projectBase}/due-diligence`
                : '/app/due-diligence',
              label: t('nav.dueDiligence'),
              description: 'Property condition and inspection history',
            },
            {
              path: projectBase ? `${projectBase}/feasibility` : '/projects',
              label: t('nav.assetFeasibility'),
              description: 'Multi-use optimizer and asset modeling',
            },
            {
              path: projectBase ? `${projectBase}/finance` : '/projects',
              label: t('nav.financialControl'),
              description: 'Development economics and financing',
            },
          ],
        },
        {
          title: 'Coordination',
          items: [
            {
              path: projectBase ? `${projectBase}/phases` : '/projects',
              label: t('nav.phaseManagement'),
              description: 'Multi-phase development sequencing',
            },
            {
              path: projectBase ? `${projectBase}/team` : '/projects',
              label: t('nav.teamCoordination'),
              description: 'Consultant coordination and approvals',
            },
            {
              path: projectBase ? `${projectBase}/regulatory` : '/projects',
              label: t('nav.regulatoryNavigation'),
              description: 'Authority submissions and compliance',
            },
          ],
        },
      )
    }

    groups.push({
      title: 'CAD',
      items: [
        {
          path: '/cad/upload',
          label: t('nav.upload'),
          description: 'Upload CAD files for analysis',
        },
        {
          path: '/cad/detection',
          label: t('nav.detection'),
          description: 'AI-powered feature detection',
        },
        {
          path: '/cad/pipelines',
          label: t('nav.pipelines'),
          description: 'Processing pipeline status',
        },
      ],
    })

    return groups
  }, [isDeveloperMode, t, projectBase])
}
