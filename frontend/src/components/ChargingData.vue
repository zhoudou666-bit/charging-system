<template>
  <div>
    <div class="page-header">
      <div>
        <h2>充电数据记录</h2>
        <p>展示充电桩上传的电压、电流、功率及风险状态，用于追踪充电行为与安全风险。</p>
      </div>

      <el-button type="primary" @click="loadData">
        刷新充电记录
      </el-button>
    </div>

    <el-table :data="dataList" border style="width: 100%; margin-top: 18px;">
      <el-table-column prop="pile_name" label="充电桩" min-width="140" />

      <el-table-column prop="location" label="位置" min-width="160" />

      <el-table-column prop="voltage" label="电压/V" width="120" />

      <el-table-column prop="current_value" label="电流/A" width="120" />

      <el-table-column prop="power" label="功率/kW" width="120" />

      <el-table-column label="状态" width="130">
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

      <el-table-column label="时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.create_time) }}
        </template>
      </el-table-column>

      <el-table-column
        v-if="props.userRole === 'admin'"
        label="操作"
        width="120"
        fixed="right"
      >
        <template #default="scope">
          <el-button
            type="danger"
            size="small"
            @click="deleteChargingData(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '../utils/time'

const props = defineProps({
  userRole: {
    type: String,
    default: 'student'
  }
})

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

const deleteChargingData = async (row) => {
  if (props.userRole !== 'admin') {
    ElMessage.warning('只有管理员可以删除充电数据记录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.pile_name} 的充电数据记录吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await axios.delete(`${API_BASE_URL}/api/charging-data/delete/${row.id}`, {
      data: {
        role: props.userRole
      }
    })

    if (res.data.code === 200) {
      ElMessage.success(res.data.message || '充电数据记录删除成功')
      await loadData()
    } else {
      ElMessage.error(res.data.message || '充电数据记录删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除充电数据失败：', error)
      ElMessage.error('删除充电数据失败，请检查后端接口')
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #0f172a;
}

.page-header p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
}
</style>