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
    await $fetch('/api/register', {
      method: 'POST',
      credentials: 'include',
      body: { username: username.value, password: password.value },
    });

    await router.push('/login');
  } catch (e) {
    if (e?.statusCode === 409) {
      error.value = 'Username already taken';
    } else {
      error.value = e?.message;
    }
    return;
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="max-w-md w-full bg-white p-8 rounded-lg shadow-lg">
      <h1 class="text-3xl font-semibold text-center mb-6">Register</h1>
      <form @submit.prevent="onSubmit" class="space-y-5">
        <div>
          <label class="block text-gray-700 mb-2">Username</label>
          <input
            v-model="username"
            type="text"
            placeholder="Choose a username"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-400"
          />
        </div>
        <div>
          <label class="block text-gray-700 mb-2">Password</label>
          <input
            v-model="password"
            type="password"
            placeholder="Create a password"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-400"
          />
        </div>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <button
          type="submit"
          class="w-full py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-md transition"
        >
          Create Account
        </button>
      </form>
      <p class="mt-4 text-center text-sm text-gray-600">
        Already have an account?
        <NuxtLink to="/login" class="text-green-600 hover:underline"
          >Login</NuxtLink
        >
      </p>
    </div>
  </div>
</template>
