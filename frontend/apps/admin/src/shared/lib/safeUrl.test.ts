/** Link từ dữ liệu cào chỉ được là http/https — xem `packages/ui/src/safeUrl.ts`. */
import { describe, expect, it } from 'vitest';
import { safeHttpUrl, safeInternalPath } from './index';

describe('safeHttpUrl', () => {
  it('giu nguyen link http/https', () => {
    expect(safeHttpUrl('https://example.com/menu')).toBe('https://example.com/menu');
    expect(safeHttpUrl('http://example.com')).toBe('http://example.com/');
    expect(safeHttpUrl('  https://example.com/a  ')).toBe('https://example.com/a');
  });

  it.each([
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    '  javascript:alert(1)',
    '\tjavascript:alert(1)',
    '\njavascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
    'ftp://example.com',
    '/duong-dan-tuong-doi',
    'www.example.com',
    '',
    '   ',
  ])('chan %j', (url) => {
    expect(safeHttpUrl(url)).toBeNull();
  });

  it('null/undefined -> null', () => {
    expect(safeHttpUrl(null)).toBeNull();
    expect(safeHttpUrl(undefined)).toBeNull();
  });
});

describe('safeInternalPath (GHSA-wrjc-x8rr-h8h6: v6 khong co ban va)', () => {
  it('giu duong dan noi bo', () => {
    expect(safeInternalPath('/account?tab=saved')).toBe('/account?tab=saved');
    expect(safeInternalPath('/')).toBe('/');
  });

  it.each([
    '//evil.com',
    '/\\evil.com',
    '/\\/evil.com',
    '\\evil.com',
    '/a\\b',
    'https://evil.com',
    'javascript:alert(1)',
    'evil.com',
    '/\tevil',
    '',
  ])('chan %j', (p) => {
    expect(safeInternalPath(p)).toBeNull();
  });

  it('khong phai chuoi -> null', () => {
    expect(safeInternalPath(undefined)).toBeNull();
    expect(safeInternalPath({ pathname: '/x' })).toBeNull();
  });
});
