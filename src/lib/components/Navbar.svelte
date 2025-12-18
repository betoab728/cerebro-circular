<script lang="ts">
  export let title = "Dashboard";
</script>

<header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 md:px-8">
  <h1 class="text-xl font-semibold text-gray-800">{title}</h1>
  
  <div class="flex items-center gap-4">
    <button class="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    </button>
  </div>
</header>
