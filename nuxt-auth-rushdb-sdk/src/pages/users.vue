<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useFetch, navigateTo } from 'nuxt/app';

const users = ref<string[]>([]);
const current = ref('');
const error = ref('');
const router = useRouter();

async function loadUsers() {
  try {
    const res = await $fetch('/api/users', {
      credentials: 'include',
    });

    users.value = res.users;
    current.value = res.current;
  } catch (e) {
    if (e?.statusCode === 401) {
      await router.push('/login');
    }

    error.value = e?.message;
    return;
  }
}

async function logout() {
  await $fetch('/api/logout', { method: 'POST', credentials: 'include' });
  navigateTo('/login');
}

onMounted(loadUsers);
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="max-w-lg w-full bg-white p-8 rounded-lg shadow-lg">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-semibold">User List</h1>
        <button
          @click="logout"
          class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md transition"
        >
          Logout
        </button>
      </div>
      <ul class="space-y-2">
        <li
          v-for="u in users"
          :key="u"
          class="px-4 py-2 rounded-md"
          :class="u === current ? 'bg-blue-100 font-medium' : 'bg-gray-100'"
        >
          {{ u }}
        </li>
      </ul>
      <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
    </div>
  </div>
</template>
