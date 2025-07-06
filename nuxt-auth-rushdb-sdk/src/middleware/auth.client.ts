import { defineNuxtRouteMiddleware, useCookie, navigateTo } from 'nuxt/app';

export default defineNuxtRouteMiddleware((to) => {
  if (['/login', '/register'].includes(to.path)) return;

  const token = useCookie('auth_token', {
    secure: true,
    readonly: true,
  });

  if (!token.value) {
    return navigateTo('/login');
  }
});
