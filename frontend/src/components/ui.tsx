import { ButtonHTMLAttributes, ReactNode } from 'react'

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

interface FieldProps {
  label: string
  children: ReactNode
  error?: string
  required?: boolean
  hint?: string
}

export function Field({ label, children, error, required, hint }: FieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-text">
        {label}
        {required && <span className="text-danger ml-1">*</span>}
      </label>
      {hint ? <p className="text-xs leading-relaxed text-muted">{hint}</p> : null}
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
