<script setup>
const props = defineProps({
  modelValue: { type: String, required: true },
  options: { type: Array, required: true },
})

const emit = defineEmits(['update:modelValue'])

function select(value) {
  if (value !== props.modelValue) {
    emit('update:modelValue', value)
  }
}
</script>

<template>
  <div class="tabs" role="tablist">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      role="tab"
      class="tab"
      :class="{ 'tab--active': option.value === modelValue }"
      :aria-selected="option.value === modelValue"
      @click="select(option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>
