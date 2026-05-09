import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

import { VoiceObservationsPanel } from '../VoiceObservationsPanel'

const mockFetchPropertyVoiceNotes = vi.fn()
const mockGetUserMedia = vi.fn()

class MockMediaRecorder {
  static instances: MockMediaRecorder[] = []

  stream: { getTracks: () => Array<{ stop: () => void }> }
  mimeType: string
  ondataavailable: ((event: { data: Blob }) => void) | null = null
  onstop: (() => void) | null = null

  constructor(
    stream: { getTracks: () => Array<{ stop: () => void }> },
    options?: { mimeType?: string },
  ) {
    this.stream = stream
    this.mimeType = options?.mimeType ?? 'audio/webm'
    MockMediaRecorder.instances.push(this)
  }

  start() {
    this.ondataavailable?.({
      data: new Blob(['voice-note'], { type: this.mimeType }),
    })
  }

  stop() {
    this.onstop?.()
  }
}

vi.mock('../../../../../api/siteAcquisition', () => ({
  fetchPropertyVoiceNotes: (propertyId: string) =>
    mockFetchPropertyVoiceNotes(propertyId),
}))

describe('VoiceObservationsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    MockMediaRecorder.instances = []

    Object.defineProperty(globalThis, 'MediaRecorder', {
      configurable: true,
      writable: true,
      value: MockMediaRecorder,
    })

    Object.defineProperty(globalThis.navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: mockGetUserMedia,
      },
    })

    globalThis.fetch = vi.fn()

    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders simplified voice note copy and surfaces saved transcripts', async () => {
    mockFetchPropertyVoiceNotes.mockResolvedValue([
      {
        voiceNoteId: 'vn-1',
        propertyId: 'prop-1',
        photoId: null,
        storageKey: 'voice/vn-1.webm',
        filename: 'site-note.webm',
        mimeType: 'audio/webm',
        fileSize: 1024,
        durationSeconds: 18,
        captureDate: '2026-04-07T08:30:00Z',
        title: 'North edge setback note',
        tags: [],
        transcript:
          'Street edge feels tighter than expected; verify frontage controls.',
        audioMetadata: null,
        publicUrl: 'https://example.com/vn-1.webm',
        location: {
          latitude: 1.3,
          longitude: 103.85,
        },
      },
    ])

    render(<VoiceObservationsPanel propertyId="prop-1" disabled />)

    expect(screen.queryByText('Voice Notes')).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /record voice note/i }),
    ).toHaveAttribute('title', 'Site notes. Transcripts appear after upload.')
    expect(screen.getByText('Voice Record')).toBeInTheDocument()
    expect(screen.queryByText('Voice capture')).not.toBeInTheDocument()
    expect(screen.queryByText('Standby')).not.toBeInTheDocument()

    expect(
      await screen.findByText(
        'Street edge feels tighter than expected; verify frontage controls.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Transcript')).toBeInTheDocument()
    expect(screen.getByText('Saved Notes (1)')).toBeInTheDocument()
  })

  it('shows transcript pending when a saved note has no transcript', async () => {
    mockFetchPropertyVoiceNotes.mockResolvedValue([
      {
        voiceNoteId: 'vn-2',
        propertyId: 'prop-1',
        photoId: null,
        storageKey: 'voice/vn-2.webm',
        filename: 'site-note.webm',
        mimeType: 'audio/webm',
        fileSize: 1024,
        durationSeconds: 12,
        captureDate: '2026-04-07T08:30:00Z',
        title: '',
        tags: [],
        transcript: '   ',
        audioMetadata: null,
        publicUrl: 'https://example.com/vn-2.webm',
        location: null,
      },
    ])

    render(<VoiceObservationsPanel propertyId="prop-1" disabled />)

    expect(await screen.findByText('Transcript pending.')).toBeInTheDocument()
  })

  it('surfaces saved-note loading failures', async () => {
    mockFetchPropertyVoiceNotes.mockRejectedValue(
      new Error('Voice API offline'),
    )

    render(<VoiceObservationsPanel propertyId="prop-1" disabled />)

    expect(await screen.findByText('Voice API offline')).toBeInTheDocument()
  })

  it('shows pending uploads and instructions when no property is captured', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-07T09:34:00Z'))
    mockFetchPropertyVoiceNotes.mockResolvedValue([])

    render(<VoiceObservationsPanel propertyId={null} />)

    await act(async () => {
      fireEvent.click(
        screen.getByRole('button', { name: /record voice note/i }),
      )
      await Promise.resolve()
    })

    expect(
      screen.getByRole('button', { name: /stop recording/i }),
    ).toBeInTheDocument()

    await act(async () => {
      vi.advanceTimersByTime(1100)
    })

    expect(
      screen.getByRole('button', { name: /stop recording/i }),
    ).toBeInTheDocument()
    expect(screen.getByText('elapsed')).toBeInTheDocument()
    expect(screen.getByText('0:01')).toBeInTheDocument()

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop recording/i }))
      await Promise.resolve()
    })

    expect(screen.getByText('Pending Uploads (1)')).toBeInTheDocument()
    expect(
      screen.getByText('Capture a property to upload recordings'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled()
  })

  it('falls back to plain-text upload errors', async () => {
    mockFetchPropertyVoiceNotes.mockResolvedValue([])
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response('Voice upload service unavailable', {
        status: 502,
        headers: { 'content-type': 'text/plain' },
      }),
    )

    render(<VoiceObservationsPanel propertyId="prop-1" />)

    await act(async () => {
      fireEvent.click(
        screen.getByRole('button', { name: /record voice note/i }),
      )
      await Promise.resolve()
    })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop recording/i }))
      await Promise.resolve()
    })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Upload' }))
      await Promise.resolve()
    })

    expect(
      await screen.findByText('Voice upload service unavailable'),
    ).toBeInTheDocument()
  })

  it('shows recording state changes in the primary control', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-07T09:34:00Z'))
    mockFetchPropertyVoiceNotes.mockResolvedValue([])

    render(<VoiceObservationsPanel propertyId="prop-1" />)

    await act(async () => {
      fireEvent.click(
        screen.getByRole('button', { name: /record voice note/i }),
      )
      await Promise.resolve()
    })

    expect(
      screen.getByRole('button', { name: /stop recording/i }),
    ).toBeInTheDocument()

    await act(async () => {
      vi.advanceTimersByTime(2100)
    })

    expect(
      screen.getByRole('button', { name: /stop recording/i }),
    ).toBeInTheDocument()
    expect(screen.getByText('0:02')).toBeInTheDocument()
    expect(screen.getByText('elapsed')).toBeInTheDocument()

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop recording/i }))
      await Promise.resolve()
    })

    expect(
      screen.getByRole('button', { name: /record voice note/i }),
    ).toBeInTheDocument()
  })
})
