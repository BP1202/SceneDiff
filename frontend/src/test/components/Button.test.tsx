import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../../components/ui/Button'

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeTruthy()
  })

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup()
    let clicked = false
    render(<Button onClick={() => { clicked = true }}>Click</Button>)
    await user.click(screen.getByText('Click'))
    expect(clicked).toBe(true)
  })

  it('is disabled when isLoading is true', () => {
    const { container } = render(<Button isLoading>Submit</Button>)
    const btn = container.querySelector('button') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it('applies correct variant class', () => {
    const { container } = render(<Button variant="danger">Delete</Button>)
    const btn = container.querySelector('button')
    expect(btn?.className).toContain('sd-button--danger')
  })

  it('applies correct size class', () => {
    const { container } = render(<Button size="lg">Large</Button>)
    const btn = container.querySelector('button')
    expect(btn?.className).toContain('sd-button--lg')
  })
})
