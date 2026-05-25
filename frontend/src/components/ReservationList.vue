<template>
  <div>
    <div class="page-header">
      <div>
        <h2>预约记录</h2>
        <p>学生预约充电后，预约有效期为 5 分钟；到期后系统自动确认充电，并生成正常充电记录。</p>
      </div>

      <el-button type="primary" @click="loadReservations">
        刷新预约记录
      </el-button>
    </div>

    <el-table :data="reservationList" border style="width: 100%; margin-top: 18px;">
      <el-table-column prop="pile_name" label="充电桩" width="160" />

      <el-table-column prop="location" label="位置" width="180" />

      <el-table-column label="预约开始时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.start_time) }}
        </template>
      </el-table-column>

      <el-table-column label="预约到期时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.end_time) }}
        </template>
      </el-table-column>

      <el-table-column label="提交预约时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.create_time) }}
        </template>
      </el-table-column>

      <el-table-column label="预约状态" width="130">
        <template #default="scope">
          <el-tag v-if="scope.row.status === '已预约'" type="success">
            已预约
          </el-tag>

          <el-tag v-else-if="scope.row.status === '已取消'" type="info">
            已取消
          </el-tag>

          <el-tag v-else-if="scope.row.status === '已充电'" type="primary">
            已充电
          </el-tag>

          <el-tag v-else type="warning">
            {{ scope.row.status }}
          </el-tag>
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
            @click="deleteReservation(scope.row)"
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { API_BASE_URL } from '../api'
import { formatDateTime } from '../utils/time'

const props = defineProps({
  userRole: {
    type: String,
    default: 'student'
  }
})

const reservationList = ref([])

const loadReservations = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/reservation/list`)
    reservationList.value = res.data.data
  } catch (error) {
    console.error('预约记录获取失败：', error)
    ElMessage.error('预约记录获取失败，请检查后端接口')
  }
}

const deleteReservation = async (row) => {
  if (props.userRole !== 'admin') {
    ElMessage.warning('只有管理员可以删除预约记录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.pile_name} 的预约记录吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await axios.delete(`${API_BASE_URL}/api/reservation/delete/${row.id}`, {
      data: {
        role: props.userRole
      }
    })

    if (res.data.code === 200) {
      ElMessage.success(res.data.message || '预约记录删除成功')
      await loadReservations()
    } else {
      ElMessage.error(res.data.message || '预约记录删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除预约记录失败：', error)
      ElMessage.error('删除预约记录失败，请检查后端接口')
    }
  }
}

onMounted(() => {
  loadReservations()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
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