<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

async function onSubmit() {
  error.value = '';

  try {
    await $fetch('/api/login', {
      method: 'POST',
      credentials: 'include',
      body: { username: username.value, password: password.value },
    });

    await router.push('/users');
  } catch (e) {
    error.value = e?.message;

    return;
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="max-w-md w-full bg-white p-8 rounded-lg shadow-lg">
      <h1 class="text-3xl font-semibold text-center mb-6">Login</h1>
      <form @submit.prevent="onSubmit" class="space-y-5">
        <div>
          <label class="block text-gray-700 mb-2">Username</label>
          <input
            v-model="username"
            type="text"
            placeholder="Your username"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <div>
          <label class="block text-gray-700 mb-2">Password</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <button
          type="submit"
          class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition"
        >
          Sign In
        </button>
      </form>
      <p class="mt-4 text-center text-sm text-gray-600">
        Don’t have an account?
        <NuxtLink to="/register" class="text-blue-600 hover:underline"
          >Register</NuxtLink
        >
      </p>
    </div>
  </div>
</template>
