<template>
  <div class="base-input">
    <input
      :type="type"
      :value="modelValue"
      @input="handleInput"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="{ 'error': errorMessage }"
    />
    <span v-if="errorMessage" class="error-message">{{ errorMessage }}</span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  validation: {
    type: Function,
    default: null
  }
});

const emit = defineEmits(['update:modelValue', 'validation-change']);

const errorMessage = ref('');

const validate = (value) => {
  if (props.validation) {
    const result = props.validation(value);
    errorMessage.value = typeof result === 'string' ? result : '';
    emit('validation-change', !errorMessage.value);
    return !errorMessage.value;
  }
  return true;
};

const handleInput = (event) => {
  const value = event.target.value;
  emit('update:modelValue', value);
  validate(value);
};

watch(() => props.modelValue, (newValue) => {
  validate(newValue);
});
</script>

<style scoped>
.base-input {
  position: relative;
  width: 100%;
  margin-bottom: 1rem;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #2e81f5;
}

input.error {
  border-color: #ff4d4f;
}

input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  position: absolute;
  left: 0;
  bottom: -1.25rem;
  color: #ff4d4f;
  font-size: 0.75rem;
}
</style> 