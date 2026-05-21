<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>校园电动车充电监测系统</h2>
      <p class="sub-title">用户登录</p>

      <el-form>
        <el-form-item label="账号">
          <el-input v-model="username" placeholder="请输入账号" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-button type="primary" style="width: 100%;" @click="login">
          登录
        </el-button>
      </el-form>

      <div class="tips">
        <p>学生账号：student / 123456</p>
        <p>管理员账号：admin / 123456</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['login-success'])

const username = ref('')
const password = ref('')

const login = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  try {
    const res = await axios.post(`${API_BASE_URL}/api/login`, {
      username: username.value,
      password: password.value
    })

    if (res.data.code === 200) {
      ElMessage.success('登录成功')
      emit('login-success', res.data.data)
    } else {
      ElMessage.error(res.data.message || '账号或密码错误')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('登录失败，请检查后端是否运行')
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #eef3f8;
}

.login-card {
  width: 420px;
  padding: 20px;
}

.login-card h2 {
  text-align: center;
  margin-bottom: 10px;
}

.sub-title {
  text-align: center;
  color: #666;
  margin-bottom: 25px;
}

.tips {
  margin-top: 20px;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}
</style>