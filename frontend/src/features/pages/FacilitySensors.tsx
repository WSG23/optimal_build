import { useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

const FLOORS = ['1', '2', '3', '4']

export default function FacilitySensorsPage() {
  const [floor, setFloor] = useState(FLOORS[0])

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.mappingLive}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Facility Sensors" className="h-full">
          <PanelBody className="flex h-full flex-col gap-4 p-4">
            <label className="flex items-center gap-2 text-sm text-white/70">
              <span>Floor</span>
              <select
                className="rounded-md border border-white/10 bg-neutral-900 px-3 py-2 text-white"
                data-testid={TID.control.floorSelector}
                value={floor}
                onChange={(event) => setFloor(event.target.value)}
              >
                {FLOORS.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex-1 rounded-md border border-white/10 bg-white/5 p-4 text-sm text-white/70">
              Showing sensors for floor {floor}
            </div>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
