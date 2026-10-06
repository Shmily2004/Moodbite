/**
 * Route vỡ (vd. tải trang lười thất bại sau deploy) phải hiện trang lỗi CỦA TA có nút tải
 * lại — không phải "Unexpected Application Error!" tiếng Anh của React Router.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { LanguageProvider } from '@/shared/i18n';
import { routes } from '../routes';
import { RouteError } from './RouteError';

function TrangVo(): JSX.Element {
  throw new Error('Failed to fetch dynamically imported module');
}

let errorSpy: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});
afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe('RouteError', () => {
  it('hien trang loi tieng Viet co nut tai lai', () => {
    const router = createMemoryRouter([
      {
        path: '/',
        element: <TrangVo />,
        errorElement: (
          <LanguageProvider>
            <RouteError />
          </LanguageProvider>
        ),
      },
    ]);
    render(<RouterProvider router={router} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Tải lại trang' })).toBeInTheDocument();
    expect(screen.queryByText(/Unexpected Application Error/)).not.toBeInTheDocument();
    expect(errorSpy).toHaveBeenCalled();
  });

  it('ban tieng Anh dich dung', () => {
    localStorage.setItem('moodbite.lang', 'en');
    const router = createMemoryRouter([
      { path: '/', element: <TrangVo />, errorElement: <LanguageProvider><RouteError /></LanguageProvider> },
    ]);
    render(<RouterProvider router={router} />);
    expect(screen.getByRole('button', { name: 'Reload page' })).toBeInTheDocument();
  });

  it('routes that da gan errorElement o goc VA o route boc cac trang', () => {
    expect(routes[0].errorElement).toBeTruthy();
    expect(routes[0].children?.[0].errorElement).toBeTruthy();
    expect(routes[0].children?.[0].path).toBeUndefined();
  });
});
