<template>
  <button
    :class="[
      'base-button',
      `type-${type}`,
      { 'loading': loading, 'disabled': disabled }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="loading-spinner"></span>
    <slot>{{ text }}</slot>
  </button>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger'].includes(value)
  },
  text: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['click']);

const handleClick = (event) => {
  emit('click', event);
};
</script>

<style scoped>
.base-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 100px;
}

.type-primary {
  background-color: #2e81f5;
  color: white;
}

.type-primary:hover {
  background-color: #2674e3;
}

.type-secondary {
  background-color: #f5f5f5;
  color: #333;
}

.type-secondary:hover {
  background-color: #e8e8e8;
}

.type-danger {
  background-color: #ff4d4f;
  color: white;
}

.type-danger:hover {
  background-color: #ff3333;
}

.disabled,
.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.disabled:hover,
.loading:hover {
  opacity: 0.7;
}

.loading-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style> 