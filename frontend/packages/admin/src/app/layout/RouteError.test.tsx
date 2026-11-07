/** Route vỡ → trang lỗi tiếng Việt có nút tải lại, không phải màn mặc định của React Router. */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { quanTriRoutes as routes } from '../routes';
import { RouteError } from './RouteError';

function TrangVo(): JSX.Element {
  throw new Error('Failed to fetch dynamically imported module');
}

afterEach(() => vi.restoreAllMocks());

describe('RouteError (admin)', () => {
  it('hien trang loi co nut tai lai', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    const router = createMemoryRouter([
      { path: '/', element: <TrangVo />, errorElement: <RouteError /> },
    ]);
    render(<RouterProvider router={router} />);
    expect(screen.getByRole('button', { name: 'Tải lại trang' })).toBeInTheDocument();
    expect(screen.queryByText(/Unexpected Application Error/)).not.toBeInTheDocument();
  });

  it('route goc da gan errorElement', () => {
    expect(routes[0].errorElement).toBeTruthy();
  });
});
