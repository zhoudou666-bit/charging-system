<template>
  <div>
    <h2>充电数据记录</h2>

    <el-button type="primary" @click="loadData">
      刷新充电记录
    </el-button>

    <el-table :data="dataList" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="pile_name" label="充电桩" />
      <el-table-column prop="location" label="位置" />
      <el-table-column prop="voltage" label="电压/V" />
      <el-table-column prop="current_value" label="电流/A" />
      <el-table-column prop="power" label="功率/kW" />

      <el-table-column label="状态">
        <template #default="scope">
          <el-tag v-if="scope.row.warning_status === '正常'" type="success">
            正常
          </el-tag>

          <el-tag v-else-if="scope.row.warning_status === '疑似过载'" type="warning">
            疑似过载
          </el-tag>

          <el-tag v-else-if="scope.row.warning_status === '严重过载'" type="danger">
            严重过载
          </el-tag>

          <el-tag v-else>
            {{ scope.row.warning_status }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="时间" min-width="180">
  <template #default="scope">
    {{ formatDateTime(scope.row.create_time) }}
  </template>
</el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '../utils/time'

const dataList = ref([])

const loadData = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/charging-data/list`)
    dataList.value = res.data.data
  } catch (error) {
    console.error('获取充电记录失败：', error)
    ElMessage.error('获取充电记录失败，请检查后端接口')
  }
}

onMounted(() => {
  loadData()
})
</script>