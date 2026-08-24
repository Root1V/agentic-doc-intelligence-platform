// Structured input for `request_input_payload` (category-a validation —
// externally-supplied data cross-checked against what's extracted). Today
// the backend only wires ONE known rule (`expected_employee_code`, see
// validation/rules/request_input_rules.py) so that gets a real field; a
// free key/value editor covers anything else `RequestInputPayload`
// accepts, since it's an open dict. As more request-input rules land
// server-side, add more structured fields here without breaking this.
import { Plus, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export interface ExtraField {
  key: string
  value: string
}

interface RequestInputFormProps {
  expectedEmployeeCode: string
  onExpectedEmployeeCodeChange: (value: string) => void
  extraFields: ExtraField[]
  onExtraFieldsChange: (fields: ExtraField[]) => void
}

export function RequestInputForm({
  expectedEmployeeCode,
  onExpectedEmployeeCodeChange,
  extraFields,
  onExtraFieldsChange,
}: RequestInputFormProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="expected-employee-code">Código de empleado esperado</Label>
        <Input
          id="expected-employee-code"
          placeholder="p. ej. 011858"
          value={expectedEmployeeCode}
          onChange={(e) => onExpectedEmployeeCodeChange(e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Se contrasta contra el <code>employee_code</code> extraído de la boleta de pago.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <Label>Otros datos (opcional)</Label>
        {extraFields.map((field, index) => (
          <div key={index} className="flex items-center gap-2">
            <Input
              placeholder="clave"
              value={field.key}
              onChange={(e) => {
                const next = [...extraFields]
                next[index] = { ...next[index], key: e.target.value }
                onExtraFieldsChange(next)
              }}
            />
            <Input
              placeholder="valor"
              value={field.value}
              onChange={(e) => {
                const next = [...extraFields]
                next[index] = { ...next[index], value: e.target.value }
                onExtraFieldsChange(next)
              }}
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-8 shrink-0"
              onClick={() => onExtraFieldsChange(extraFields.filter((_, i) => i !== index))}
            >
              <X className="size-3.5" />
            </Button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="self-start"
          onClick={() => onExtraFieldsChange([...extraFields, { key: '', value: '' }])}
        >
          <Plus className="size-3.5" />
          Agregar otro dato
        </Button>
      </div>
    </div>
  )
}
