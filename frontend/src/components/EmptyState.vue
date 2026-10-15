<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="empty card">
    <h3 class="display-sm empty__title">{{ title }}</h3>
    <p v-if="description" class="empty__description">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  text-align: center;
  padding: var(--space-xxl) var(--space-xl);
}

.empty__title {
  color: var(--color-ink);
}

.empty__description {
  margin-top: var(--space-sm);
  font-size: var(--text-body-sm);
  color: var(--color-muted);
}
</style>
