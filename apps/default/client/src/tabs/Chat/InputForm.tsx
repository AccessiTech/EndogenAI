import { useRef, useState, type FormEvent, type KeyboardEvent } from 'react'

interface InputFormProps {
  onSubmit: (message: string) => void
  disabled: boolean
}

/**
 * Chat input form.
 *
 * WCAG:
 * - <label> with htmlFor associates label with textarea
 * - Enter sends; Shift+Enter inserts newline
 * - disabled state propagated to both input and button
 * - send button has explicit aria-label
 * - Touch target >= 44x44px enforced via CSS
 */
export function InputForm({ onSubmit, disabled }: InputFormProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
    // Auto-resize back to single line
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
  }

  return (
    <div className="chat-input-area">
      <form
        className="chat-input-form"
        onSubmit={handleSubmit}
        aria-label="Send a message"
      >
        <label htmlFor="chat-input" className="sr-only">
          Message
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
          aria-label="Message input"
          aria-multiline="true"
          disabled={disabled}
          rows={1}
          autoComplete="off"
          spellCheck
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
        >
          Send
        </button>
      </form>
    </div>
  )
}
