<template>
  <div class="platform-advanced">
    <el-alert type="info" :closable="false" show-icon class="mb-[8px]">
      <template #title>
        管理员配置：平台主表、平台品牌、平台质量、平台区域、平台供应商；用户配置：用户平台配置。
      </template>
    </el-alert>
    <el-tabs v-model="activeTab">
      <el-tab-pane v-if="isAdminConfigVisible" label="管理员配置-平台主表" name="platform">
        <el-form :inline="true" :model="platformQuery" class="mb-[8px]">
          <el-form-item label="平台编码">
            <el-input v-model="platformQuery.platformCode" clearable />
          </el-form-item>
          <el-form-item label="平台名称">
            <el-input v-model="platformQuery.platformName" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="queryPlatformList">查询</el-button>
            <el-button @click="resetPlatformQuery">重置</el-button>
            <el-button type="success" @click="openPlatformDialog()">新增平台</el-button>
          </el-form-item>
        </el-form>
        <el-table v-loading="platformLoading" :data="platformList" border>
          <el-table-column label="ID" prop="id" width="90" />
          <el-table-column label="平台编码" prop="platformCode" min-width="120" />
          <el-table-column label="平台名称" prop="platformName" min-width="140" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button link type="primary" @click="openPlatformDialog(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removePlatform(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="platformTotal > 0"
          v-model:page="platformQuery.pageNum"
          v-model:limit="platformQuery.pageSize"
          :total="platformTotal"
          @pagination="getPlatformList"
        />
      </el-tab-pane>

      <el-tab-pane v-if="isAdminConfigVisible" label="管理员配置-平台品牌" name="brand">
        <el-form :inline="true" :model="brandQuery" class="mb-[8px]">
          <el-form-item label="平台">
            <el-select v-model="brandQuery.platformId" clearable filterable style="width: 180px">
              <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="品牌名称">
            <el-input v-model="brandQuery.brandName" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="queryBrandList">查询</el-button>
            <el-button @click="resetBrandQuery">重置</el-button>
            <el-button type="success" @click="openBrandDialog()">新增平台品牌</el-button>
          </el-form-item>
        </el-form>
        <el-table v-loading="brandLoading" :data="brandList" border>
          <el-table-column label="ID" prop="id" width="90" />
          <el-table-column label="平台" min-width="140">
            <template #default="scope">
              {{ getPlatformName(scope.row.platformId) }}
            </template>
          </el-table-column>
          <el-table-column label="品牌名称" prop="brandName" min-width="140" />
          <el-table-column label="品牌原始ID" prop="brandOriginId" min-width="160" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button link type="primary" @click="openBrandDialog(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removeBrand(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="brandTotal > 0"
          v-model:page="brandQuery.pageNum"
          v-model:limit="brandQuery.pageSize"
          :total="brandTotal"
          @pagination="getBrandList"
        />
      </el-tab-pane>

      <el-tab-pane v-if="isAdminConfigVisible" label="管理员配置-平台质量" name="quality">
        <el-form :inline="true" :model="qualityQuery" class="mb-[8px]">
          <el-form-item label="平台">
            <el-select v-model="qualityQuery.platformId" clearable filterable style="width: 180px">
              <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="质量编码">
            <el-input v-model="qualityQuery.qualityCode" clearable />
          </el-form-item>
          <el-form-item label="质量名称">
            <el-input v-model="qualityQuery.qualityName" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="queryQualityList">查询</el-button>
            <el-button @click="resetQualityQuery">重置</el-button>
            <el-button type="success" @click="openQualityDialog()">新增平台质量</el-button>
          </el-form-item>
        </el-form>
        <el-table v-loading="qualityLoading" :data="qualityList" border>
          <el-table-column label="ID" prop="id" width="90" />
          <el-table-column label="平台" min-width="140">
            <template #default="scope">
              {{ getPlatformName(scope.row.platformId) }}
            </template>
          </el-table-column>
          <el-table-column label="质量编码" prop="qualityCode" min-width="120" />
          <el-table-column label="质量名称" prop="qualityName" min-width="140" />
          <el-table-column label="质量原始ID" prop="qualityOriginId" min-width="150" />
          <el-table-column label="质量类型" prop="qualityType" width="100" />
          <el-table-column label="排序" prop="orderNum" width="90" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button link type="primary" @click="openQualityDialog(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removeQuality(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="qualityTotal > 0"
          v-model:page="qualityQuery.pageNum"
          v-model:limit="qualityQuery.pageSize"
          :total="qualityTotal"
          @pagination="getQualityList"
        />
      </el-tab-pane>

      <el-tab-pane v-if="isAdminConfigVisible" label="管理员配置-平台区域" name="region">
        <el-form :inline="true" :model="regionQuery" class="mb-[8px]">
          <el-form-item label="平台">
            <el-select v-model="regionQuery.platformId" clearable filterable style="width: 180px">
              <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="区域名称">
            <el-input v-model="regionQuery.regionName" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="queryRegionList">查询</el-button>
            <el-button @click="resetRegionQuery">重置</el-button>
            <el-button type="success" @click="openRegionDialog()">新增平台区域</el-button>
          </el-form-item>
        </el-form>
        <el-table v-loading="regionLoading" :data="regionList" border>
          <el-table-column label="ID" prop="id" width="90" />
          <el-table-column label="平台" min-width="140">
            <template #default="scope">
              {{ getPlatformName(scope.row.platformId) }}
            </template>
          </el-table-column>
          <el-table-column label="区域名称" prop="regionName" min-width="140" />
          <el-table-column label="区域原始ID" prop="regionOriginId" min-width="160" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button link type="primary" @click="openRegionDialog(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removeRegion(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="regionTotal > 0"
          v-model:page="regionQuery.pageNum"
          v-model:limit="regionQuery.pageSize"
          :total="regionTotal"
          @pagination="getRegionList"
        />
      </el-tab-pane>

      <el-tab-pane v-if="isAdminConfigVisible" label="管理员配置-平台供应商" name="supplier">
        <el-form :inline="true" :model="supplierQuery" class="mb-[8px]">
          <el-form-item label="平台">
            <el-select v-model="supplierQuery.platformId" clearable filterable style="width: 180px" @change="onSupplierQueryPlatformChange">
              <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="供应商名称">
            <el-input v-model="supplierQuery.supplierName" clearable />
          </el-form-item>
          <el-form-item label="区域">
            <el-select v-model="supplierQuery.regionId" clearable filterable style="width: 180px">
              <el-option v-for="item in supplierRegionOptions" :key="item.id" :label="item.regionName" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="querySupplierList">查询</el-button>
            <el-button @click="resetSupplierQuery">重置</el-button>
            <el-button type="success" @click="openSupplierDialog()">新增平台供应商</el-button>
          </el-form-item>
        </el-form>
        <el-table v-loading="supplierLoading" :data="supplierList" border>
          <el-table-column label="ID" prop="id" width="90" />
          <el-table-column label="平台" min-width="140">
            <template #default="scope">
              {{ getPlatformName(scope.row.platformId) }}
            </template>
          </el-table-column>
          <el-table-column label="供应商名称" prop="supplierName" min-width="140" />
          <el-table-column label="供应商原始ID" prop="supplierOriginId" min-width="160" />
          <el-table-column label="区域" prop="regionName" min-width="140" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button link type="primary" @click="openSupplierDialog(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removeSupplier(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="supplierTotal > 0"
          v-model:page="supplierQuery.pageNum"
          v-model:limit="supplierQuery.pageSize"
          :total="supplierTotal"
          @pagination="getSupplierList"
        />
      </el-tab-pane>

      <el-tab-pane label="用户配置-用户平台配置" name="userConfig">
        <el-form :inline="true" :model="userConfigQuery" class="mb-[8px]">
          <el-form-item label="用户ID">
            <el-input-number v-model="userConfigQuery.userId" :min="1" :controls="false" :disabled="!isAdminConfigVisible" />
          </el-form-item>
          <el-form-item label="平台编码">
            <el-input v-model="userConfigQuery.platformCode" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="queryUserConfigList">查询</el-button>
            <el-button @click="resetUserConfigQuery">重置</el-button>
            <el-button type="success" @click="openUserConfigDialog()">新增用户配置</el-button>
          </el-form-item>
        </el-form>
        <el-table v-loading="userConfigLoading" :data="userConfigList" border>
          <el-table-column label="ID" prop="id" width="90" />
          <el-table-column label="用户ID" prop="userId" width="100" />
          <el-table-column label="平台编码" prop="platformCode" min-width="120" />
          <el-table-column label="默认城市" prop="defaultCity" min-width="120" />
          <el-table-column label="价格优势率" prop="priceAdvantageRate" width="120" />
          <el-table-column label="默认加价率" prop="defaultMarkupRate" width="120" />
          <el-table-column label="默认调货天数" prop="defaultTransferDays" width="120" />
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button link type="primary" @click="openUserConfigDialog(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removeUserConfig(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="userConfigTotal > 0"
          v-model:page="userConfigQuery.pageNum"
          v-model:limit="userConfigQuery.pageSize"
          :total="userConfigTotal"
          @pagination="getUserConfigList"
        />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="platformDialogVisible" :title="platformForm.id ? '编辑平台' : '新增平台'" width="520px">
      <el-form ref="platformFormRef" :model="platformForm" :rules="platformRules" label-width="92px">
        <el-form-item label="平台编码" prop="platformCode">
          <el-input v-model="platformForm.platformCode" />
        </el-form-item>
        <el-form-item label="平台名称" prop="platformName">
          <el-input v-model="platformForm.platformName" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="platformForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="platformDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitPlatform">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="brandDialogVisible" :title="brandForm.id ? '编辑平台品牌' : '新增平台品牌'" width="520px">
      <el-form ref="brandFormRef" :model="brandForm" :rules="brandRules" label-width="92px">
        <el-form-item label="平台" prop="platformId">
          <el-select v-model="brandForm.platformId" style="width: 100%" filterable>
            <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌名称" prop="brandName">
          <el-input v-model="brandForm.brandName" />
        </el-form-item>
        <el-form-item label="品牌原始ID" prop="brandOriginId">
          <el-input v-model="brandForm.brandOriginId" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="brandForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brandDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitBrand">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="qualityDialogVisible" :title="qualityForm.id ? '编辑平台质量' : '新增平台质量'" width="560px">
      <el-form ref="qualityFormRef" :model="qualityForm" :rules="qualityRules" label-width="100px">
        <el-form-item label="平台" prop="platformId">
          <el-select v-model="qualityForm.platformId" style="width: 100%" filterable>
            <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="质量编码" prop="qualityCode">
          <el-input v-model="qualityForm.qualityCode" />
        </el-form-item>
        <el-form-item label="质量名称" prop="qualityName">
          <el-input v-model="qualityForm.qualityName" />
        </el-form-item>
        <el-form-item label="质量原始ID" prop="qualityOriginId">
          <el-input v-model="qualityForm.qualityOriginId" />
        </el-form-item>
        <el-form-item label="质量类型">
          <el-input-number v-model="qualityForm.qualityType" :min="0" :max="99" style="width: 100%" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="qualityForm.orderNum" :min="0" :max="9999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="qualityForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="qualityDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitQuality">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="regionDialogVisible" :title="regionForm.id ? '编辑平台区域' : '新增平台区域'" width="520px">
      <el-form ref="regionFormRef" :model="regionForm" :rules="regionRules" label-width="92px">
        <el-form-item label="平台" prop="platformId">
          <el-select v-model="regionForm.platformId" style="width: 100%" filterable>
            <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域名称" prop="regionName">
          <el-input v-model="regionForm.regionName" />
        </el-form-item>
        <el-form-item label="区域原始ID" prop="regionOriginId">
          <el-input v-model="regionForm.regionOriginId" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="regionForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="regionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitRegion">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="supplierDialogVisible" :title="supplierForm.id ? '编辑平台供应商' : '新增平台供应商'" width="560px">
      <el-form ref="supplierFormRef" :model="supplierForm" :rules="supplierRules" label-width="100px">
        <el-form-item label="平台" prop="platformId">
          <el-select v-model="supplierForm.platformId" style="width: 100%" filterable @change="onSupplierFormPlatformChange">
            <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商名称" prop="supplierName">
          <el-input v-model="supplierForm.supplierName" />
        </el-form-item>
        <el-form-item label="供应商原始ID" prop="supplierOriginId">
          <el-input v-model="supplierForm.supplierOriginId" />
        </el-form-item>
        <el-form-item label="区域">
          <el-select v-model="supplierForm.regionId" clearable filterable style="width: 100%">
            <el-option v-for="item in supplierFormRegionOptions" :key="item.id" :label="item.regionName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="supplierForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supplierDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitSupplier">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="userConfigDialogVisible" :title="userConfigForm.id ? '编辑用户平台配置' : '新增用户平台配置'" width="720px">
      <el-form ref="userConfigFormRef" :model="userConfigForm" :rules="userConfigRules" label-width="128px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="用户ID" prop="userId">
              <el-input-number v-model="userConfigForm.userId" :min="1" :controls="false" :disabled="!isAdminConfigVisible" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="平台" prop="platformId">
              <el-select v-model="userConfigForm.platformId" style="width: 100%" filterable @change="onUserConfigPlatformChange">
                <el-option v-for="item in platformOptions" :key="item.id" :label="item.platformName" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="平台编码" prop="platformCode">
              <el-input v-model="userConfigForm.platformCode" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认城市">
              <el-input v-model="userConfigForm.defaultCity" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="价格优势率">
              <el-input-number v-model="userConfigForm.priceAdvantageRate" :precision="2" :step="0.5" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认加价率">
              <el-input-number v-model="userConfigForm.defaultMarkupRate" :precision="4" :step="0.01" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="默认调货天数">
              <el-input-number v-model="userConfigForm.defaultTransferDays" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="抓取数量上限">
              <el-input-number v-model="userConfigForm.singleSkuMaxCrawlCount" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="userConfigDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitUserConfig">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import {
  addPartCrawlerPlatform,
  addPartCrawlerPlatformBrand,
  addPartCrawlerPlatformQuality,
  addPartCrawlerPlatformRegion,
  addPartCrawlerPlatformSupplier,
  addUserPartCrawlerPlatformConfig,
  deletePartCrawlerPlatform,
  deletePartCrawlerPlatformBrand,
  deletePartCrawlerPlatformQuality,
  deletePartCrawlerPlatformRegion,
  deletePartCrawlerPlatformSupplier,
  deleteUserPartCrawlerPlatformConfig,
  listPartCrawlerPlatformBrands,
  listPartCrawlerPlatformOptions,
  listPartCrawlerPlatformQualities,
  listPartCrawlerPlatformRegions,
  listPartCrawlerPlatformSuppliers,
  listPartCrawlerPlatforms,
  listUserPartCrawlerPlatformConfigs,
  updatePartCrawlerPlatform,
  updatePartCrawlerPlatformBrand,
  updatePartCrawlerPlatformQuality,
  updatePartCrawlerPlatformRegion,
  updatePartCrawlerPlatformSupplier,
  updateUserPartCrawlerPlatformConfig
} from '@/api/kaisi/base-config';
import {
  PartCrawlerPlatformBrandForm,
  PartCrawlerPlatformBrandQuery,
  PartCrawlerPlatformBrandVO,
  PartCrawlerPlatformForm,
  PartCrawlerPlatformQuery,
  PartCrawlerPlatformQualityForm,
  PartCrawlerPlatformQualityQuery,
  PartCrawlerPlatformQualityVO,
  PartCrawlerPlatformRegionForm,
  PartCrawlerPlatformRegionQuery,
  PartCrawlerPlatformRegionVO,
  PartCrawlerPlatformSupplierForm,
  PartCrawlerPlatformSupplierQuery,
  PartCrawlerPlatformSupplierVO,
  PartCrawlerPlatformVO,
  UserPartCrawlerPlatformConfigForm,
  UserPartCrawlerPlatformConfigQuery,
  UserPartCrawlerPlatformConfigVO
} from '@/api/kaisi/base-config/types';
import { FormInstance, FormRules } from 'element-plus';
import { checkPermi } from '@/utils/permission';
import { useUserStore } from '@/store/modules/user';

const { proxy } = getCurrentInstance() as ComponentInternalInstance;
const activeTab = ref('platform');
const submitLoading = ref(false);
const userStore = useUserStore();
const isAdminConfigVisible = computed(() => checkPermi(['kaisi:base-config:edit']));

// 平台主表
const platformLoading = ref(false);
const platformTotal = ref(0);
const platformList = ref<PartCrawlerPlatformVO[]>([]);
const platformOptions = ref<PartCrawlerPlatformVO[]>([]);
const platformQuery = reactive<PartCrawlerPlatformQuery>({ pageNum: 1, pageSize: 10 });
const platformDialogVisible = ref(false);
const platformFormRef = ref<FormInstance>();
const platformForm = reactive<PartCrawlerPlatformForm>({ platformCode: '', platformName: '', status: 1 });
const platformRules = reactive<FormRules>({
  platformCode: [{ required: true, message: '请输入平台编码', trigger: 'blur' }],
  platformName: [{ required: true, message: '请输入平台名称', trigger: 'blur' }]
});

// 平台品牌
const brandLoading = ref(false);
const brandTotal = ref(0);
const brandList = ref<PartCrawlerPlatformBrandVO[]>([]);
const brandQuery = reactive<PartCrawlerPlatformBrandQuery>({ pageNum: 1, pageSize: 10 });
const brandDialogVisible = ref(false);
const brandFormRef = ref<FormInstance>();
const brandForm = reactive<PartCrawlerPlatformBrandForm>({ platformId: undefined, brandName: '', brandOriginId: '', status: 1 });
const brandRules = reactive<FormRules>({
  platformId: [{ required: true, message: '请选择平台', trigger: 'change' }],
  brandName: [{ required: true, message: '请输入品牌名称', trigger: 'blur' }],
  brandOriginId: [{ required: true, message: '请输入品牌原始ID', trigger: 'blur' }]
});

// 平台质量
const qualityLoading = ref(false);
const qualityTotal = ref(0);
const qualityList = ref<PartCrawlerPlatformQualityVO[]>([]);
const qualityQuery = reactive<PartCrawlerPlatformQualityQuery>({ pageNum: 1, pageSize: 10 });
const qualityDialogVisible = ref(false);
const qualityFormRef = ref<FormInstance>();
const qualityForm = reactive<PartCrawlerPlatformQualityForm>({
  platformId: undefined,
  qualityCode: '',
  qualityName: '',
  qualityOriginId: '',
  qualityType: 0,
  orderNum: 0,
  status: 1
});
const qualityRules = reactive<FormRules>({
  platformId: [{ required: true, message: '请选择平台', trigger: 'change' }],
  qualityCode: [{ required: true, message: '请输入质量编码', trigger: 'blur' }],
  qualityName: [{ required: true, message: '请输入质量名称', trigger: 'blur' }],
  qualityOriginId: [{ required: true, message: '请输入质量原始ID', trigger: 'blur' }]
});

// 平台区域
const regionLoading = ref(false);
const regionTotal = ref(0);
const regionList = ref<PartCrawlerPlatformRegionVO[]>([]);
const regionQuery = reactive<PartCrawlerPlatformRegionQuery>({ pageNum: 1, pageSize: 10 });
const regionDialogVisible = ref(false);
const regionFormRef = ref<FormInstance>();
const regionForm = reactive<PartCrawlerPlatformRegionForm>({
  platformId: undefined,
  regionName: '',
  regionOriginId: '',
  status: 1
});
const regionRules = reactive<FormRules>({
  platformId: [{ required: true, message: '请选择平台', trigger: 'change' }],
  regionName: [{ required: true, message: '请输入区域名称', trigger: 'blur' }],
  regionOriginId: [{ required: true, message: '请输入区域原始ID', trigger: 'blur' }]
});

// 平台供应商
const supplierLoading = ref(false);
const supplierTotal = ref(0);
const supplierList = ref<PartCrawlerPlatformSupplierVO[]>([]);
const supplierQuery = reactive<PartCrawlerPlatformSupplierQuery>({ pageNum: 1, pageSize: 10 });
const supplierDialogVisible = ref(false);
const supplierFormRef = ref<FormInstance>();
const supplierForm = reactive<PartCrawlerPlatformSupplierForm>({
  platformId: undefined,
  supplierName: '',
  supplierOriginId: '',
  regionId: undefined,
  status: 1
});
const supplierRules = reactive<FormRules>({
  platformId: [{ required: true, message: '请选择平台', trigger: 'change' }],
  supplierName: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  supplierOriginId: [{ required: true, message: '请输入供应商原始ID', trigger: 'blur' }]
});
const supplierRegionOptions = ref<PartCrawlerPlatformRegionVO[]>([]);
const supplierFormRegionOptions = ref<PartCrawlerPlatformRegionVO[]>([]);

// 用户平台配置
const userConfigLoading = ref(false);
const userConfigTotal = ref(0);
const userConfigList = ref<UserPartCrawlerPlatformConfigVO[]>([]);
const userConfigQuery = reactive<UserPartCrawlerPlatformConfigQuery>({ pageNum: 1, pageSize: 10 });
const userConfigDialogVisible = ref(false);
const userConfigFormRef = ref<FormInstance>();
const userConfigForm = reactive<UserPartCrawlerPlatformConfigForm>({
  userId: undefined,
  platformId: undefined,
  platformCode: '',
  defaultCity: '',
  priceAdvantageRate: 5,
  defaultMarkupRate: 0,
  defaultTransferDays: 0,
  singleSkuMaxCrawlCount: 0,
  crawlStrategyType: 'FULL_SELECTED',
  crawlStrategyStopOnHit: false
});
const userConfigRules = reactive<FormRules>({
  userId: [{ required: true, message: '请输入用户ID', trigger: 'blur' }],
  platformId: [{ required: true, message: '请选择平台', trigger: 'change' }],
  platformCode: [{ required: true, message: '请输入平台编码', trigger: 'blur' }]
});

const getPlatformName = (platformId?: number) => {
  const selected = platformOptions.value.find((item) => item.id === platformId);
  return selected?.platformName || platformId || '-';
};

const loadPlatformOptions = async () => {
  const { data } = await listPartCrawlerPlatformOptions();
  platformOptions.value = data || [];
};

const getPlatformList = async () => {
  platformLoading.value = true;
  const res = await listPartCrawlerPlatforms(platformQuery);
  platformList.value = res.rows || [];
  platformTotal.value = res.total || 0;
  platformLoading.value = false;
};

const queryPlatformList = () => {
  platformQuery.pageNum = 1;
  getPlatformList();
};

const resetPlatformQuery = () => {
  platformQuery.platformCode = '';
  platformQuery.platformName = '';
  platformQuery.status = undefined;
  queryPlatformList();
};

const openPlatformDialog = (row?: PartCrawlerPlatformVO) => {
  if (row) {
    platformForm.id = row.id;
    platformForm.platformCode = row.platformCode;
    platformForm.platformName = row.platformName;
    platformForm.status = row.status;
  } else {
    platformForm.id = undefined;
    platformForm.platformCode = '';
    platformForm.platformName = '';
    platformForm.status = 1;
  }
  platformDialogVisible.value = true;
};

const submitPlatform = async () => {
  await platformFormRef.value?.validate();
  submitLoading.value = true;
  if (platformForm.id) {
    await updatePartCrawlerPlatform(platformForm);
  } else {
    await addPartCrawlerPlatform(platformForm);
  }
  submitLoading.value = false;
  platformDialogVisible.value = false;
  await loadPlatformOptions();
  await getPlatformList();
};

const removePlatform = async (id: number) => {
  await proxy?.$modal.confirm('确认删除该平台吗？');
  await deletePartCrawlerPlatform(id);
  proxy?.$modal.msgSuccess('删除成功');
  await loadPlatformOptions();
  await Promise.all([getPlatformList(), getBrandList(), getQualityList(), getRegionList(), getSupplierList()]);
};

const getBrandList = async () => {
  brandLoading.value = true;
  const res = await listPartCrawlerPlatformBrands(brandQuery);
  brandList.value = res.rows || [];
  brandTotal.value = res.total || 0;
  brandLoading.value = false;
};

const queryBrandList = () => {
  brandQuery.pageNum = 1;
  getBrandList();
};

const resetBrandQuery = () => {
  brandQuery.platformId = undefined;
  brandQuery.brandName = '';
  brandQuery.brandOriginId = '';
  brandQuery.status = undefined;
  queryBrandList();
};

const openBrandDialog = (row?: PartCrawlerPlatformBrandVO) => {
  if (row) {
    brandForm.id = row.id;
    brandForm.platformId = row.platformId;
    brandForm.brandName = row.brandName;
    brandForm.brandOriginId = row.brandOriginId;
    brandForm.status = row.status;
  } else {
    brandForm.id = undefined;
    brandForm.platformId = undefined;
    brandForm.brandName = '';
    brandForm.brandOriginId = '';
    brandForm.status = 1;
  }
  brandDialogVisible.value = true;
};

const submitBrand = async () => {
  await brandFormRef.value?.validate();
  submitLoading.value = true;
  if (brandForm.id) {
    await updatePartCrawlerPlatformBrand(brandForm);
  } else {
    await addPartCrawlerPlatformBrand(brandForm);
  }
  submitLoading.value = false;
  brandDialogVisible.value = false;
  await getBrandList();
};

const removeBrand = async (id: number) => {
  await proxy?.$modal.confirm('确认删除该平台品牌吗？');
  await deletePartCrawlerPlatformBrand(id);
  proxy?.$modal.msgSuccess('删除成功');
  await getBrandList();
};

const getQualityList = async () => {
  qualityLoading.value = true;
  const res = await listPartCrawlerPlatformQualities(qualityQuery);
  qualityList.value = res.rows || [];
  qualityTotal.value = res.total || 0;
  qualityLoading.value = false;
};

const queryQualityList = () => {
  qualityQuery.pageNum = 1;
  getQualityList();
};

const resetQualityQuery = () => {
  qualityQuery.platformId = undefined;
  qualityQuery.qualityCode = '';
  qualityQuery.qualityName = '';
  qualityQuery.qualityOriginId = '';
  qualityQuery.status = undefined;
  queryQualityList();
};

const openQualityDialog = (row?: PartCrawlerPlatformQualityVO) => {
  if (row) {
    qualityForm.id = row.id;
    qualityForm.platformId = row.platformId;
    qualityForm.qualityCode = row.qualityCode;
    qualityForm.qualityName = row.qualityName;
    qualityForm.qualityOriginId = row.qualityOriginId;
    qualityForm.qualityType = row.qualityType;
    qualityForm.orderNum = row.orderNum;
    qualityForm.status = row.status;
  } else {
    qualityForm.id = undefined;
    qualityForm.platformId = undefined;
    qualityForm.qualityCode = '';
    qualityForm.qualityName = '';
    qualityForm.qualityOriginId = '';
    qualityForm.qualityType = 0;
    qualityForm.orderNum = 0;
    qualityForm.status = 1;
  }
  qualityDialogVisible.value = true;
};

const submitQuality = async () => {
  await qualityFormRef.value?.validate();
  submitLoading.value = true;
  if (qualityForm.id) {
    await updatePartCrawlerPlatformQuality(qualityForm);
  } else {
    await addPartCrawlerPlatformQuality(qualityForm);
  }
  submitLoading.value = false;
  qualityDialogVisible.value = false;
  await getQualityList();
};

const removeQuality = async (id: number) => {
  await proxy?.$modal.confirm('确认删除该平台质量吗？');
  await deletePartCrawlerPlatformQuality(id);
  proxy?.$modal.msgSuccess('删除成功');
  await getQualityList();
};

const getRegionList = async () => {
  regionLoading.value = true;
  const res = await listPartCrawlerPlatformRegions(regionQuery);
  regionList.value = res.rows || [];
  regionTotal.value = res.total || 0;
  regionLoading.value = false;
};

const queryRegionList = () => {
  regionQuery.pageNum = 1;
  getRegionList();
};

const resetRegionQuery = () => {
  regionQuery.platformId = undefined;
  regionQuery.regionName = '';
  regionQuery.regionOriginId = '';
  regionQuery.status = undefined;
  queryRegionList();
};

const openRegionDialog = (row?: PartCrawlerPlatformRegionVO) => {
  if (row) {
    regionForm.id = row.id;
    regionForm.platformId = row.platformId;
    regionForm.regionName = row.regionName;
    regionForm.regionOriginId = row.regionOriginId;
    regionForm.status = row.status;
  } else {
    regionForm.id = undefined;
    regionForm.platformId = undefined;
    regionForm.regionName = '';
    regionForm.regionOriginId = '';
    regionForm.status = 1;
  }
  regionDialogVisible.value = true;
};

const submitRegion = async () => {
  await regionFormRef.value?.validate();
  submitLoading.value = true;
  if (regionForm.id) {
    await updatePartCrawlerPlatformRegion(regionForm);
  } else {
    await addPartCrawlerPlatformRegion(regionForm);
  }
  submitLoading.value = false;
  regionDialogVisible.value = false;
  await getRegionList();
};

const removeRegion = async (id: number) => {
  await proxy?.$modal.confirm('确认删除该平台区域吗？');
  await deletePartCrawlerPlatformRegion(id);
  proxy?.$modal.msgSuccess('删除成功');
  await getRegionList();
};

const loadRegionOptionsByPlatform = async (platformId?: number) => {
  if (!platformId) {
    return [] as PartCrawlerPlatformRegionVO[];
  }
  const res = await listPartCrawlerPlatformRegions({ pageNum: 1, pageSize: 1000, platformId, status: 1 });
  return res.rows || [];
};

const getSupplierList = async () => {
  supplierLoading.value = true;
  const res = await listPartCrawlerPlatformSuppliers(supplierQuery);
  supplierList.value = res.rows || [];
  supplierTotal.value = res.total || 0;
  supplierLoading.value = false;
};

const querySupplierList = () => {
  supplierQuery.pageNum = 1;
  getSupplierList();
};

const resetSupplierQuery = () => {
  supplierQuery.platformId = undefined;
  supplierQuery.supplierName = '';
  supplierQuery.supplierOriginId = '';
  supplierQuery.regionId = undefined;
  supplierQuery.status = undefined;
  supplierRegionOptions.value = [];
  querySupplierList();
};

const onSupplierQueryPlatformChange = async (platformId?: number) => {
  supplierQuery.regionId = undefined;
  supplierRegionOptions.value = await loadRegionOptionsByPlatform(platformId);
};

const openSupplierDialog = async (row?: PartCrawlerPlatformSupplierVO) => {
  if (row) {
    supplierForm.id = row.id;
    supplierForm.platformId = row.platformId;
    supplierForm.supplierName = row.supplierName;
    supplierForm.supplierOriginId = row.supplierOriginId;
    supplierForm.regionId = row.regionId;
    supplierForm.status = row.status;
    supplierFormRegionOptions.value = await loadRegionOptionsByPlatform(row.platformId);
  } else {
    supplierForm.id = undefined;
    supplierForm.platformId = undefined;
    supplierForm.supplierName = '';
    supplierForm.supplierOriginId = '';
    supplierForm.regionId = undefined;
    supplierForm.status = 1;
    supplierFormRegionOptions.value = [];
  }
  supplierDialogVisible.value = true;
};

const onSupplierFormPlatformChange = async (platformId?: number) => {
  supplierForm.regionId = undefined;
  supplierFormRegionOptions.value = await loadRegionOptionsByPlatform(platformId);
};

const submitSupplier = async () => {
  await supplierFormRef.value?.validate();
  submitLoading.value = true;
  if (supplierForm.id) {
    await updatePartCrawlerPlatformSupplier(supplierForm);
  } else {
    await addPartCrawlerPlatformSupplier(supplierForm);
  }
  submitLoading.value = false;
  supplierDialogVisible.value = false;
  await getSupplierList();
};

const removeSupplier = async (id: number) => {
  await proxy?.$modal.confirm('确认删除该平台供应商吗？');
  await deletePartCrawlerPlatformSupplier(id);
  proxy?.$modal.msgSuccess('删除成功');
  await getSupplierList();
};

const getUserConfigList = async () => {
  userConfigLoading.value = true;
  const res = await listUserPartCrawlerPlatformConfigs(userConfigQuery);
  userConfigList.value = res.rows || [];
  userConfigTotal.value = res.total || 0;
  userConfigLoading.value = false;
};

const queryUserConfigList = () => {
  userConfigQuery.pageNum = 1;
  getUserConfigList();
};

const resetUserConfigQuery = () => {
  userConfigQuery.userId = isAdminConfigVisible.value ? undefined : Number(userStore.userId) || undefined;
  userConfigQuery.platformId = undefined;
  userConfigQuery.platformCode = '';
  queryUserConfigList();
};

const openUserConfigDialog = (row?: UserPartCrawlerPlatformConfigVO) => {
  if (row) {
    userConfigForm.id = row.id;
    userConfigForm.userId = row.userId;
    userConfigForm.platformId = row.platformId;
    userConfigForm.platformCode = row.platformCode;
    userConfigForm.defaultCity = row.defaultCity;
    userConfigForm.priceAdvantageRate = row.priceAdvantageRate;
    userConfigForm.defaultMarkupRate = row.defaultMarkupRate;
    userConfigForm.defaultTransferDays = row.defaultTransferDays;
    userConfigForm.singleSkuMaxCrawlCount = row.singleSkuMaxCrawlCount;
    userConfigForm.regionExtraDaysJson = row.regionExtraDaysJson;
    userConfigForm.qualityOriginIdsJson = row.qualityOriginIdsJson;
    userConfigForm.brandOriginIdsJson = row.brandOriginIdsJson;
    userConfigForm.regionOriginIdsJson = row.regionOriginIdsJson;
    userConfigForm.supplierConfigsJson = row.supplierConfigsJson;
    userConfigForm.crawlStrategyType = row.crawlStrategyType;
    userConfigForm.crawlStrategySelectedPlatformCodesJson = row.crawlStrategySelectedPlatformCodesJson;
    userConfigForm.crawlStrategyPriorityPlatformCodesJson = row.crawlStrategyPriorityPlatformCodesJson;
    userConfigForm.crawlStrategyStopOnHit = row.crawlStrategyStopOnHit;
  } else {
    userConfigForm.id = undefined;
    userConfigForm.userId = isAdminConfigVisible.value ? undefined : Number(userStore.userId) || undefined;
    userConfigForm.platformId = undefined;
    userConfigForm.platformCode = '';
    userConfigForm.defaultCity = '';
    userConfigForm.priceAdvantageRate = 5;
    userConfigForm.defaultMarkupRate = 0;
    userConfigForm.defaultTransferDays = 0;
    userConfigForm.singleSkuMaxCrawlCount = 0;
    userConfigForm.regionExtraDaysJson = '';
    userConfigForm.qualityOriginIdsJson = '';
    userConfigForm.brandOriginIdsJson = '';
    userConfigForm.regionOriginIdsJson = '';
    userConfigForm.supplierConfigsJson = '';
    userConfigForm.crawlStrategyType = 'FULL_SELECTED';
    userConfigForm.crawlStrategySelectedPlatformCodesJson = '';
    userConfigForm.crawlStrategyPriorityPlatformCodesJson = '';
    userConfigForm.crawlStrategyStopOnHit = false;
  }
  userConfigDialogVisible.value = true;
};

const onUserConfigPlatformChange = (platformId: number) => {
  const selected = platformOptions.value.find((item) => item.id === platformId);
  if (selected && !userConfigForm.platformCode) {
    userConfigForm.platformCode = selected.platformCode;
  }
};

const submitUserConfig = async () => {
  await userConfigFormRef.value?.validate();
  submitLoading.value = true;
  if (userConfigForm.id) {
    await updateUserPartCrawlerPlatformConfig(userConfigForm);
  } else {
    await addUserPartCrawlerPlatformConfig(userConfigForm);
  }
  submitLoading.value = false;
  userConfigDialogVisible.value = false;
  await getUserConfigList();
};

const removeUserConfig = async (id: number) => {
  await proxy?.$modal.confirm('确认删除该用户平台配置吗？');
  await deleteUserPartCrawlerPlatformConfig(id);
  proxy?.$modal.msgSuccess('删除成功');
  await getUserConfigList();
};

onMounted(async () => {
  if (!isAdminConfigVisible.value) {
    activeTab.value = 'userConfig';
    userConfigQuery.userId = Number(userStore.userId) || undefined;
  }
  await loadPlatformOptions();
  if (isAdminConfigVisible.value) {
    await Promise.all([getPlatformList(), getBrandList(), getQualityList(), getRegionList(), getSupplierList(), getUserConfigList()]);
    return;
  }
  await getUserConfigList();
});
</script>

<style scoped lang="scss">
.platform-advanced {
  padding-top: 4px;
}
</style>
