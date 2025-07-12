import { defineNuxtRouteMiddleware, useCookie, navigateTo } from 'nuxt/app';

export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie('auth_token', {
    secure: true,
    readonly: true,
  });

  if (['/login', '/register'].includes(to.path)) {
    return token.value ? navigateTo('/users') : undefined;
  }

  if (!token.value) {
    return navigateTo('/login');
  }
});
