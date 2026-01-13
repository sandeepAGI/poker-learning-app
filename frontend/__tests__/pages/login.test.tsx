/**
 * Test login/register page.
 * Phase 2.2: Login/Register Pages
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LoginPage from '@/app/login/page';
import { login, register } from '@/lib/auth';
import { useRouter } from 'next/navigation';

jest.mock('@/lib/auth');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn()
}));

describe('Login Page', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  });

  describe('Initial Render', () => {
    it('should render login form by default', () => {
      render(<LoginPage />);

      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^login$/i })).toBeInTheDocument();
    });

    it('should show register option', () => {
      render(<LoginPage />);

      expect(screen.getByText(/create one/i)).toBeInTheDocument();
    });
  });

  describe('Login Flow', () => {
    it('should handle successful login', async () => {
      (login as jest.Mock).mockResolvedValue({
        token: 'token',
        user_id: 'user-1',
        username: 'testuser'
      });

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' }
      });

      fireEvent.click(screen.getByRole('button', { name: /^login$/i }));

      await waitFor(() => {
        expect(login).toHaveBeenCalledWith('testuser', 'password123');
        expect(mockPush).toHaveBeenCalledWith('/');
      });
    });

    it('should show error on login failure', async () => {
      (login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'wrong' }
      });

      fireEvent.click(screen.getByRole('button', { name: /^login$/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('should disable button while loading', async () => {
      (login as jest.Mock).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' }
      });

      const button = screen.getByRole('button', { name: /^login$/i });
      fireEvent.click(button);

      expect(button).toBeDisabled();
    });
  });

  describe('Register Flow', () => {
    it('should switch to register mode', () => {
      render(<LoginPage />);

      fireEvent.click(screen.getByText(/create one/i));

      expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^register$/i })).toBeInTheDocument();
    });

    it('should handle successful registration', async () => {
      (register as jest.Mock).mockResolvedValue({
        token: 'token',
        user_id: 'user-1',
        username: 'newuser'
      });

      render(<LoginPage />);

      fireEvent.click(screen.getByText(/create one/i));

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'newuser' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' }
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' }
      });

      fireEvent.click(screen.getByRole('button', { name: /^register$/i }));

      await waitFor(() => {
        expect(register).toHaveBeenCalledWith('newuser', 'password123');
        expect(mockPush).toHaveBeenCalledWith('/');
      });
    });

    it('should validate password match', async () => {
      render(<LoginPage />);

      fireEvent.click(screen.getByText(/create one/i));

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' }
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'different' }
      });

      fireEvent.click(screen.getByRole('button', { name: /^register$/i }));

      await waitFor(() => {
        expect(screen.getByText(/passwords.*match/i)).toBeInTheDocument();
        expect(register).not.toHaveBeenCalled();
      });
    });

    it('should validate empty fields', async () => {
      render(<LoginPage />);

      fireEvent.click(screen.getByRole('button', { name: /^login$/i }));

      await waitFor(() => {
        expect(screen.getByText(/required/i)).toBeInTheDocument();
      });
    });
  });

  describe('Mode Switching', () => {
    it('should clear error when switching modes', async () => {
      (login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'test' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'test' }
      });
      fireEvent.click(screen.getByRole('button', { name: /^login$/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/create one/i));

      expect(screen.queryByText(/invalid/i)).not.toBeInTheDocument();
    });
  });
});
