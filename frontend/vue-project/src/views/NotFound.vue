<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <router-link to="/" class="home-link">返回首页</router-link>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
}

h1 {
  font-size: 6rem;
  margin: 0;
  color: #4CAF50;
}

p {
  font-size: 1.5rem;
  margin: 1rem 0;
  color: #666;
}

.home-link {
  color: #4CAF50;
  text-decoration: none;
  font-size: 1rem;
  padding: 0.5rem 1rem;
  border: 1px solid #4CAF50;
  border-radius: 4px;
  margin-top: 1rem;
}

.home-link:hover {
  background-color: #4CAF50;
  color: white;
}
</style> 