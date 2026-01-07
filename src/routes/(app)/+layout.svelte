<script lang="ts">
	import Sidebar from '$lib/components/Sidebar.svelte';
	import "../../app.css";
	import favicon from '$lib/assets/favicon.svg';
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { browser } from '$app/environment';

	let { children } = $props();

    onMount(() => {
        if (browser) {
            const token = localStorage.getItem('token');
            if (!token) {
                goto('/login');
            }
        }
    });
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen bg-gray-50 flex">
	<Sidebar />
	<main class="flex-1 md:ml-64 min-h-screen flex flex-col transition-all duration-300 w-full">
		{@render children()}
	</main>
</div>
