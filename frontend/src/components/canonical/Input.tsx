import {
  TextField,
  TextFieldProps,
  styled,
  InputAdornment,
} from '@mui/material'
import { forwardRef, ReactNode } from 'react'

export interface InputProps extends Omit<TextFieldProps, 'variant'> {
  /**
   * Visual variant
   */
  variant?: 'default' | 'filled'
  /**
   * Leading icon/element
   */
  startAdornment?: ReactNode
  /**
   * Trailing icon/element
   */
  endAdornment?: ReactNode
}

const StyledTextField = styled(TextField, {
  shouldForwardProp: (prop) => prop !== 'inputVariant',
})<{
  inputVariant?: 'default' | 'filled'
}>(({ inputVariant }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: 'var(--ob-radius-sm)', // 4px - ENFORCED
    background:
      inputVariant === 'filled'
        ? 'var(--ob-color-surface-strong)'
        : 'transparent',
    transition: 'all 0.2s ease',

    '& fieldset': {
      border: 'var(--ob-border-fine-strong)',
      transition: 'border-color 0.2s ease',
    },

    '&:hover fieldset': {
      border: 'var(--ob-border-fine-hover)',
    },

    '&.Mui-focused fieldset': {
      border: '1px solid var(--ob-color-border-brand)',
      boxShadow: 'var(--ob-glow-brand-subtle)',
    },

    '&.Mui-error fieldset': {
      border: '1px solid var(--ob-color-border-error)',
    },

    '&.Mui-disabled': {
      opacity: 0.5,
      '& fieldset': {
        border: 'var(--ob-border-fine)',
      },
    },
  },

  '& .MuiOutlinedInput-input': {
    color: 'var(--ob-color-text-primary)',
    fontSize: 'var(--ob-font-size-sm)',
    padding: 'var(--ob-space-075) var(--ob-space-100)',
    height: 'auto',
    lineHeight: 1.5,

    '&::placeholder': {
      color: 'var(--ob-color-text-muted)',
      opacity: 1,
    },
  },

  '& .MuiInputLabel-root': {
    color: 'var(--ob-color-text-secondary)',
    fontSize: 'var(--ob-font-size-sm)',

    '&.Mui-focused': {
      color: 'var(--ob-color-brand-primary)',
    },

    '&.Mui-error': {
      color: 'var(--ob-color-status-error-text)',
    },
  },

  '& .MuiFormHelperText-root': {
    color: 'var(--ob-color-text-muted)',
    fontSize: 'var(--ob-font-size-xs)',
    marginLeft: 0,
    marginTop: 'var(--ob-space-025)',

    '&.Mui-error': {
      color: 'var(--ob-color-status-error-text)',
    },
  },

  '& .MuiInputAdornment-root': {
    color: 'var(--ob-color-text-muted)',

    '& svg': {
      fontSize: 18,
    },
  },
}))

/**
 * Input - Square Cyber-Minimalism Form Field
 *
 * Geometry: 4px border radius (--ob-radius-sm)
 * Height: 40px
 * Border: 1px fine line strong, brand on focus
 *
 * Wraps MUI TextField with consistent styling.
 */
export const Input = forwardRef<HTMLDivElement, InputProps>(
  (
    {
      variant = 'default',
      startAdornment,
      endAdornment,
      InputProps: inputProps,
      ...props
    },
    ref,
  ) => {
    return (
      <StyledTextField
        ref={ref}
        inputVariant={variant}
        variant="outlined"
        fullWidth
        InputProps={{
          ...inputProps,
          startAdornment: startAdornment ? (
            <InputAdornment position="start">{startAdornment}</InputAdornment>
          ) : (
            inputProps?.startAdornment
          ),
          endAdornment: endAdornment ? (
            <InputAdornment position="end">{endAdornment}</InputAdornment>
          ) : (
            inputProps?.endAdornment
          ),
        }}
        {...props}
      />
    )
  },
)

Input.displayName = 'Input'
