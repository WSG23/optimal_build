import {
  useEffect,
  useMemo,
  useState,
  type ChangeEvent,
  type FormEvent,
} from 'react'
import {
  fetchChecklistTemplates,
  createChecklistTemplate,
  updateChecklistTemplate,
  deleteChecklistTemplate,
  importChecklistTemplates,
  type ChecklistTemplate,
  type ChecklistTemplateDraft,
  type ChecklistTemplateUpdate,
  type ChecklistTemplateImportResult,
  type ChecklistCategory,
  type ChecklistPriority,
} from '../../../api/siteAcquisition'
import { Link } from '../../../router'

interface FormState {
  id: string | null
  developmentScenario: string
  category: ChecklistCategory
  itemTitle: string
  itemDescription: string
  priority: ChecklistPriority
  typicalDurationDays: string
  requiresProfessional: boolean
  professionalType: string
  displayOrder: string
}

interface ImportState {
  text: string
  replaceExisting: boolean
}

const CATEGORY_OPTIONS: ChecklistCategory[] = [
  'title_verification',
  'zoning_compliance',
  'environmental_assessment',
  'structural_survey',
  'heritage_constraints',
  'utility_capacity',
  'access_rights',
]

const PRIORITY_OPTIONS: ChecklistPriority[] = ['critical', 'high', 'medium', 'low']
const SCENARIO_SUGGESTIONS = [
  'raw_land',
  'existing_building',
  'heritage_property',
  'underused_asset',
  'mixed_use_redevelopment',
]

const INITIAL_FORM: FormState = {
  id: null,
  developmentScenario: 'raw_land',
  category: 'title_verification',
  itemTitle: '',
  itemDescription: '',
  priority: 'high',
  typicalDurationDays: '',
  requiresProfessional: false,
  professionalType: '',
  displayOrder: '',
}

const INITIAL_IMPORT_STATE: ImportState = {
  text: '',
  replaceExisting: false,
}

function normaliseDraftFromRecord(
  record: Record<string, unknown>,
): ChecklistTemplateDraft {
  const canonical: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(record)) {
    const headerKey = normaliseHeader(key)
    canonical[headerKey] = typeof value === 'string' ? stripQuotes(value) : value
  }

  const developmentScenario = String(
    canonical.developmentScenario ?? '',
  ).trim()
  const category = String(canonical.category ?? 'title_verification')
    .trim()
    .toLowerCase() as ChecklistCategory
  const itemTitle = String(canonical.itemTitle ?? '').trim()
  const itemDescriptionRaw =
    canonical.itemDescription ?? ''
  const priority = String(canonical.priority ?? 'medium')
    .trim()
    .toLowerCase() as ChecklistPriority
  const typicalDurationRaw =
    canonical.typicalDurationDays
  const requiresProfessionalRaw = canonical.requiresProfessional
  const professionalTypeRaw = canonical.professionalType ?? ''
  const displayOrderRaw = canonical.displayOrder

  const typicalDuration =
    typeof typicalDurationRaw === 'number'
      ? typicalDurationRaw
      : typeof typicalDurationRaw === 'string' && typicalDurationRaw.trim() !== ''
      ? Number(typicalDurationRaw)
      : undefined

  const requiresProfessional = Boolean(requiresProfessionalRaw)
  const professionalType = requiresProfessional
    ? String(professionalTypeRaw ?? '').trim() || null
    : null

  const displayOrder =
    typeof displayOrderRaw === 'number'
      ? displayOrderRaw
      : typeof displayOrderRaw === 'string' && displayOrderRaw.trim() !== ''
      ? Number(displayOrderRaw)
      : undefined

  return {
    developmentScenario,
    category,
    itemTitle,
    itemDescription:
      typeof itemDescriptionRaw === 'string' && itemDescriptionRaw.trim() !== ''
        ? itemDescriptionRaw.trim()
        : undefined,
    priority,
    typicalDurationDays:
      typeof typicalDuration === 'number' && Number.isFinite(typicalDuration)
        ? typicalDuration
        : undefined,
    requiresProfessional,
    professionalType,
    displayOrder:
      typeof displayOrder === 'number' && Number.isFinite(displayOrder)
        ? displayOrder
        : undefined,
  }
}

function parseImportInput(text: string): ChecklistTemplateDraft[] {
  const trimmed = text.trim()
  if (!trimmed) {
    return []
  }

  try {
    const parsed = JSON.parse(trimmed)
    if (Array.isArray(parsed)) {
      return parsed.map((entry) =>
        normaliseDraftFromRecord(entry as Record<string, unknown>),
      )
    }
    if (
      typeof parsed === 'object' &&
      parsed !== null &&
      Array.isArray((parsed as Record<string, unknown>).templates)
    ) {
      return (parsed as { templates: Record<string, unknown>[] }).templates.map(
        (entry) =>
          normaliseDraftFromRecord(entry as Record<string, unknown>),
      )
    }
    throw new Error(
      'JSON payload must be an array of templates or an object with a `templates` array.',
    )
  } catch (jsonError) {
    if (
      jsonError instanceof Error &&
      jsonError.message.startsWith('JSON payload must')
    ) {
      throw jsonError
    }
    // fall back to CSV parsing
  }

  const lines = trimmed.split(/\r?\n/).filter((line) => line.trim() !== '')
  if (lines.length === 0) {
    return []
  }

  const [headerLine, ...rows] = lines
  const rawHeaders = headerLine.split(',')
  const headers = rawHeaders.map((header) => normaliseHeader(header))

  for (const required of REQUIRED_HEADERS) {
    if (!headers.includes(required)) {
      throw new Error(
        `CSV must include the following headers: ${REQUIRED_HEADERS.join(', ')}`,
      )
    }
  }

  return rows.map((row) => {
    const columns = row.split(',')
    const record: Record<string, unknown> = {}

    headers.forEach((key, idx) => {
      const rawValue = columns[idx] ?? ''
      record[key] = stripQuotes(rawValue)
    })

    return normaliseDraftFromRecord(record)
  })
}

function buildDraftFromForm(form: FormState): ChecklistTemplateDraft {
  return {
    developmentScenario: form.developmentScenario.trim(),
    category: form.category,
    itemTitle: form.itemTitle.trim(),
    itemDescription: form.itemDescription.trim() || undefined,
    priority: form.priority,
    typicalDurationDays:
      form.typicalDurationDays.trim() === ''
        ? undefined
        : Number(form.typicalDurationDays),
    requiresProfessional: form.requiresProfessional,
    professionalType: form.requiresProfessional
      ? form.professionalType.trim() || null
      : null,
    displayOrder:
      form.displayOrder.trim() === '' ? undefined : Number(form.displayOrder),
  }
}

export function ChecklistTemplateManager() {
  const [templates, setTemplates] = useState<ChecklistTemplate[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(INITIAL_FORM)
  const [importState, setImportState] = useState<ImportState>(INITIAL_IMPORT_STATE)
  const [selectedScenario, setSelectedScenario] = useState<string>('all')
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null)

  async function loadTemplates() {
    setIsLoading(true)
    setError(null)
    const data = await fetchChecklistTemplates()
    setTemplates(data)
    setIsLoading(false)
  }

  useEffect(() => {
    void loadTemplates()
  }, [])

  const scenarios = useMemo(() => {
    const unique = new Set<string>()
    templates.forEach((template) => {
      unique.add(template.developmentScenario)
    })
    return ['all', ...Array.from(unique).sort()]
  }, [templates])

  const filteredTemplates = useMemo(() => {
    if (selectedScenario === 'all') {
      return templates
    }
    return templates.filter(
      (template) => template.developmentScenario === selectedScenario,
    )
  }, [templates, selectedScenario])

  function resetForm() {
    setForm(INITIAL_FORM)
    setEditingTemplateId(null)
  }

  function handleEdit(template: ChecklistTemplate) {
    setForm({
      id: template.id,
      developmentScenario: template.developmentScenario,
      category: template.category,
      itemTitle: template.itemTitle,
      itemDescription: template.itemDescription ?? '',
      priority: template.priority,
      typicalDurationDays: template.typicalDurationDays
        ? String(template.typicalDurationDays)
        : '',
      requiresProfessional: template.requiresProfessional,
      professionalType: template.professionalType ?? '',
      displayOrder: template.displayOrder ? String(template.displayOrder) : '',
    })
    setEditingTemplateId(template.id)
    setSelectedScenario(template.developmentScenario)
    setFeedback(null)
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  async function handleDelete(template: ChecklistTemplate) {
    const confirmed = window.confirm(
      `Delete "${template.itemTitle}" for scenario ${template.developmentScenario}?`,
    )
    if (!confirmed) {
      return
    }

    const removed = await deleteChecklistTemplate(template.id)
    if (!removed) {
      setError('Failed to delete template.')
      return
    }

    setFeedback('Template deleted successfully.')
    await loadTemplates()
    if (form.id === template.id) {
      resetForm()
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setFeedback(null)

    if (!form.itemTitle.trim()) {
      setError('Template title is required.')
      return
    }

    const draft = buildDraftFromForm(form)

    let result: ChecklistTemplate | null = null
    if (form.id) {
      const updates: ChecklistTemplateUpdate = {
        ...draft,
      }
      result = await updateChecklistTemplate(form.id, updates)
      if (!result) {
        setError('Failed to update template.')
        return
      }
      setFeedback('Template updated successfully.')
    } else {
      result = await createChecklistTemplate(draft)
      if (!result) {
        setError('Failed to create template.')
        return
      }
      setFeedback('Template created successfully.')
    }

    await loadTemplates()
    setSelectedScenario(result.developmentScenario)
    resetForm()
  }

  async function handleImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setFeedback(null)

    try {
      const drafts = parseImportInput(importState.text)
      if (drafts.length === 0) {
        setError('No templates detected in input.')
        return
      }
      const outcome: ChecklistTemplateImportResult | null =
        await importChecklistTemplates(drafts, importState.replaceExisting)
      if (!outcome) {
        setError('Bulk import failed. Check the console for details.')
        return
      }
      setFeedback(
        `Imported templates — created: ${outcome.created}, updated: ${outcome.updated}, deleted: ${outcome.deleted}.`,
      )
      setImportState(INITIAL_IMPORT_STATE)
      await loadTemplates()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to parse input.'
      setError(message)
    }
  }

  function handleFormChange(
    event: ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >,
  ) {
    const { name, value, type } = event.target
    const checked = 'checked' in event.target ? event.target.checked : false
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  function handleImportChange(
    event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) {
    const { name, value, type } = event.target
    const checked = 'checked' in event.target ? event.target.checked : false
    setImportState((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  return (
    <div className="site-acquisition-template-manager">
      <header className="template-manager-header">
        <div>
          <h1>Due diligence checklist templates</h1>
          <p>
            Create, edit, and bulk import scenario-specific checklist templates.
            Changes take effect immediately for new properties.
          </p>
        </div>
        <Link className="template-manager-back" to="/app/site-acquisition">
          ← Back to site acquisition workspace
        </Link>
      </header>

      {error && <div className="template-manager-alert error">{error}</div>}
      {feedback && (
        <div className="template-manager-alert success">{feedback}</div>
      )}

      <section className="template-manager-section">
        <div className="template-manager-controls">
          <label>
            Scenario filter
            <select
              value={selectedScenario}
              onChange={(event) => {
                setSelectedScenario(event.target.value)
              }}
            >
              {scenarios.map((scenario) => (
                <option key={scenario} value={scenario}>
                  {scenario === 'all' ? 'All scenarios' : scenario}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={loadTemplates} disabled={isLoading}>
            Refresh
          </button>
        </div>

        {isLoading ? (
          <p>Loading templates…</p>
        ) : filteredTemplates.length === 0 ? (
          <p className="template-manager-empty">
            No templates found for the selected scenario.
          </p>
        ) : (
          <table className="template-manager-table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Category</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Duration (days)</th>
                <th>Requires professional</th>
                <th>Order</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTemplates.map((template) => (
                <tr key={template.id}>
                  <td>{template.developmentScenario}</td>
                  <td>{template.category}</td>
                  <td>{template.itemTitle}</td>
                  <td>{template.priority}</td>
                  <td>{template.typicalDurationDays ?? '—'}</td>
                  <td>{template.requiresProfessional ? 'Yes' : 'No'}</td>
                  <td>{template.displayOrder}</td>
                  <td className="template-manager-actions">
                    <button type="button" onClick={() => handleEdit(template)}>
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(template)}
                      className="danger"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="template-manager-section">
        <div className="template-manager-form-heading">
          <h2>{editingTemplateId ? 'Edit template' : 'Create template'}</h2>
          {editingTemplateId && (
            <span className="template-manager-pill">Editing</span>
          )}
        </div>
        <form className="template-manager-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              Scenario
              <input
                list="scenario-suggestions"
                name="developmentScenario"
                value={form.developmentScenario}
                onChange={handleFormChange}
                required
              />
            </label>
            <datalist id="scenario-suggestions">
              {SCENARIO_SUGGESTIONS.map((scenario) => (
                <option key={scenario} value={scenario} />
              ))}
            </datalist>

            <label>
              Category
              <select
                name="category"
                value={form.category}
                onChange={handleFormChange}
              >
                {CATEGORY_OPTIONS.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Priority
              <select
                name="priority"
                value={form.priority}
                onChange={handleFormChange}
              >
                {PRIORITY_OPTIONS.map((priority) => (
                  <option key={priority} value={priority}>
                    {priority}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Typical duration (days)
              <input
                name="typicalDurationDays"
                value={form.typicalDurationDays}
                onChange={handleFormChange}
                type="number"
                min="0"
              />
            </label>

            <label className="checkbox">
              <input
                type="checkbox"
                name="requiresProfessional"
                checked={form.requiresProfessional}
                onChange={handleFormChange}
              />
              Requires specialist support
            </label>

            <label>
              Professional type
              <input
                name="professionalType"
                value={form.professionalType}
                onChange={handleFormChange}
                disabled={!form.requiresProfessional}
              />
            </label>

            <label>
              Display order
              <input
                name="displayOrder"
                value={form.displayOrder}
                onChange={handleFormChange}
                type="number"
                min="0"
              />
            </label>
          </div>

          <label>
            Checklist item title
            <input
              name="itemTitle"
              value={form.itemTitle}
              onChange={handleFormChange}
              required
            />
          </label>

          <label>
            Checklist item description
            <textarea
              name="itemDescription"
              value={form.itemDescription}
              onChange={handleFormChange}
              rows={3}
            />
          </label>

          <div className="template-manager-form-actions">
            <button type="submit">{form.id ? 'Update template' : 'Create template'}</button>
            {form.id && (
              <button
                type="button"
                className="secondary"
                onClick={resetForm}
              >
                Cancel editing
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="template-manager-section">
        <h2>Bulk import</h2>
        <p>
          Paste JSON or CSV content. CSV must include headers
          <code>
            developmentScenario, category, itemTitle, priority, itemDescription,
            typicalDurationDays, requiresProfessional, professionalType,
            displayOrder
          </code>
          . When <strong>replace existing</strong> is checked, any templates for
          scenarios present in the import but missing from the payload will be
          removed.
        </p>
        <form className="template-manager-import" onSubmit={handleImport}>
          <textarea
            name="text"
            value={importState.text}
            onChange={handleImportChange}
            rows={8}
            placeholder="Paste JSON array or CSV rows here"
          />
          <label className="checkbox">
            <input
              type="checkbox"
              name="replaceExisting"
              checked={importState.replaceExisting}
              onChange={handleImportChange}
            />
            Replace existing templates for imported scenarios
          </label>
          <div className="template-manager-form-actions">
            <button type="submit">Import templates</button>
          </div>
        </form>
        <details className="template-manager-sample">
          <summary>Sample CSV</summary>
          <pre>
            {`developmentScenario,category,itemTitle,priority,typicalDurationDays,requiresProfessional,professionalType,displayOrder
raw_land,title_verification,Verify title records,critical,5,true,Conveyancing lawyer,10
raw_land,environmental_assessment,Commission soil testing,high,7,true,Geotechnical engineer,20`}
          </pre>
        </details>
      </section>
    </div>
  )
}

export default ChecklistTemplateManager
const HEADER_ALIASES: Record<string, string> = {
  developmentscenario: 'developmentScenario',
  'development scenario': 'developmentScenario',
  development_scenario: 'developmentScenario',
  category: 'category',
  itemtitle: 'itemTitle',
  'item title': 'itemTitle',
  item_title: 'itemTitle',
  itemdescription: 'itemDescription',
  'item description': 'itemDescription',
  item_description: 'itemDescription',
  priority: 'priority',
  typicaldurationdays: 'typicalDurationDays',
  'typical duration days': 'typicalDurationDays',
  typical_duration_days: 'typicalDurationDays',
  requiresprofessional: 'requiresProfessional',
  'requires professional': 'requiresProfessional',
  requires_professional: 'requiresProfessional',
  professionaltype: 'professionalType',
  'professional type': 'professionalType',
  professional_type: 'professionalType',
  displayorder: 'displayOrder',
  'display order': 'displayOrder',
  display_order: 'displayOrder',
}

const REQUIRED_HEADERS = [
  'developmentScenario',
  'category',
  'itemTitle',
  'priority',
]

function stripQuotes(value: string): string {
  const trimmed = value.trim().replace(/^\uFEFF/, '')
  if (trimmed.length >= 2) {
    const first = trimmed[0]
    const last = trimmed[trimmed.length - 1]
    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return trimmed.slice(1, -1)
    }
  }
  return trimmed
}

function normaliseHeader(value: string): string {
  const stripped = stripQuotes(value)
  const lower = stripped.toLowerCase()
  return HEADER_ALIASES[lower] ?? stripped
}
