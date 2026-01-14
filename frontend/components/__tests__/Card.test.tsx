import { render, screen } from '@testing-library/react';
import { Card } from '../Card';

describe('Card Component', () => {
  it('renders card with suit and rank', () => {
    render(<Card card="Ah" data-testid="test-card" />);
    expect(screen.getByTestId('test-card')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('♥')).toBeInTheDocument();
  });

  it('renders hidden card', () => {
    render(<Card card="Ah" hidden={true} data-testid="hidden-card" />);
    expect(screen.getByTestId('hidden-card')).toBeInTheDocument();
    expect(screen.queryByText('A')).not.toBeInTheDocument();
  });

  it('renders with stable key prop', () => {
    const { rerender } = render(<Card key="player-1-card-0" card="Ah" />);
    rerender(<Card key="player-1-card-0" card="Ah" />);
    // Should not cause unmount/remount
    expect(screen.getByText('A')).toBeInTheDocument();
  });
});
