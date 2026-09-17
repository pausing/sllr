import { ButtonHTMLAttributes, ReactNode, useEffect, useId, useRef, useState } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'ghost' | 'danger'
  children: ReactNode
}

export function Button({ variant = 'default', className = '', children, ...props }: ButtonProps) {
  const baseStyles = 'px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variantStyles = {
    default: 'bg-raised text-text border border-line hover:bg-[#222936]',
    primary: 'bg-accent text-ink hover:opacity-90',
    ghost: 'text-muted hover:text-text hover:bg-raised',
    danger: 'bg-danger text-white hover:bg-danger-hover',
  }
  
  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

interface InfoTipProps {
  label: string
  text: string
  align?: 'start' | 'end'
}

export function InfoTip({ label, text, align = 'start' }: InfoTipProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLSpanElement>(null)
  const tooltipId = useId()

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    window.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <span
      ref={rootRef}
      className="relative inline-flex align-middle"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-muted hover:bg-raised hover:text-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        aria-label={`About ${label}`}
        aria-expanded={open}
        aria-describedby={open ? tooltipId : undefined}
        onClick={() => setOpen((current) => !current)}
        onFocus={() => setOpen(true)}
      >
        <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" aria-hidden="true" fill="currentColor">
          <path d="M10 1.7a8.3 8.3 0 1 0 0 16.6 8.3 8.3 0 0 0 0-16.6zm0 4.1a1.05 1.05 0 1 1 0 2.1 1.05 1.05 0 0 1 0-2.1zm1.15 8.35h-2.3V8.7h2.3v5.45z" />
        </svg>
      </button>
      {open ? (
        <span
          id={tooltipId}
          role="tooltip"
          className={`absolute z-30 mt-1 w-64 max-w-[min(16rem,calc(100vw-2.5rem))] rounded-md border border-line bg-raised px-3 py-2 text-left text-xs font-normal leading-relaxed text-muted shadow-lg top-full left-0 ${
            align === 'end' ? 'md:left-auto md:right-0' : ''
          }`}
        >
          {text}
        </span>
      ) : null}
    </span>
  )
}

interface FieldProps {
  label: string
  children: ReactNode
  error?: string
  required?: boolean
  hint?: string
  info?: string
  infoAlign?: 'start' | 'end'
}

export function Field({ label, children, error, required, hint, info, infoAlign }: FieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex min-h-6 items-center gap-1">
        <span className="text-sm font-medium text-text">
          {label}
          {required ? <span className="ml-1 text-danger">*</span> : null}
        </span>
        {info ? <InfoTip label={label} text={info} align={infoAlign} /> : null}
      </div>
      {hint && !info ? <p className="text-xs leading-relaxed text-muted">{hint}</p> : null}
      {children}
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  )
}

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export function TextInput({ className = '', ...props }: TextInputProps) {
  return (
    <input
      className={`w-full px-3 py-2 bg-panel border border-line rounded-md text-text placeholder-muted focus:outline-none focus:border-accent ${className}`}
      {...props}
    />
  )
}

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export function TextArea({ className = '', ...props }: TextAreaProps) {
  return (
    <textarea
      className={`w-full px-3 py-2 bg-panel border border-line rounded-md text-text placeholder-muted focus:outline-none focus:border-accent ${className}`}
      rows={3}
      {...props}
    />
  )
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string; label: string }[]
}

export function Select({ options, className = '', ...props }: SelectProps) {
  return (
    <select
      className={`w-full px-3 py-2 bg-panel border border-line rounded-md text-text focus:outline-none focus:border-accent ${className}`}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}

interface CardProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-panel border border-line rounded-lg p-4 md:p-6 ${className}`}>
      {children}
    </div>
  )
}

interface StatusDotProps {
  status: string
}

export function StatusDot({ status }: StatusDotProps) {
  const colors: Record<string, string> = {
    Draft: 'bg-muted',
    Approved: 'bg-accent',
    'Not Implemented': 'bg-amber',
    Implemented: 'bg-green-500',
  }
  
  return (
    <span className="inline-flex items-center gap-2 text-sm">
      <span className={`w-2 h-2 rounded-full ${colors[status] || 'bg-muted'}`} />
      {status}
    </span>
  )
}
