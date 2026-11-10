"""
API 序列化器

序列化器负责模型实例与前端数据之间的双向转换，并把字段校验集中在这里，
视图（控制器）只处理 HTTP 语义，不再重复写校验逻辑。
"""

from rest_framework import serializers

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """
    咨询留言序列化器（读写）。

    字段与前端 `ContactPage.vue` 的表单一一对应：
    称呼 / 联系电话 / 所在城市 / 需求类型 / 预算区间 / 需求描述。

    `id`、`created_at` 由服务端维护，前端即使在请求体里带上也会被忽略。
    `status`（跟进状态）在这里是可写的，供管理员通过 API 更新。
    """

    # 显式声明两个下拉字段，选项直接取自模型，
    # 保证与前端 `demandTypes` / `budgets` 始终一致
    demand_type = serializers.ChoiceField(
        label='需求类型',
        choices=Contact.DEMAND_TYPE_CHOICES,
        required=False,
        allow_blank=True,
    )
    budget = serializers.ChoiceField(
        label='预算区间',
        choices=Contact.BUDGET_CHOICES,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Contact
        fields = [
            'id',
            'name',
            'phone',
            'city',
            'demand_type',
            'budget',
            'description',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ContactCreateSerializer(ContactSerializer):
    """
    公开提交用的序列化器。

    与 `ContactSerializer` 的唯一区别：`status` 不可写。
    访客提交时即便在请求体里塞了 `status`，也会被忽略，
    避免前端伪造跟进状态。
    """

    class Meta(ContactSerializer.Meta):
        read_only_fields = ['id', 'status', 'created_at']
