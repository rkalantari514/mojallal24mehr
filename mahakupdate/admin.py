from django.contrib import admin

from accounting.models import BedehiMoshtari
from mahakupdate.models import Mtables, Kala, Factor, FactorDetaile, WordCount, Category, Kardex, Person, KalaGroupinfo, \
    Storagek, Mojodi, Sanad, SanadDetail, AccCoding, ChequesRecieve, MyCondition, ChequesPay, Bank, Loan, LoanDetil


# Register your models here.


class MtablesAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'name', 'description', 'in_use', 'update_priority', 'last_update_time', 'row_count',
                    'cloumn_count']
    # list_filter = ['description','name', 'in_use']
    list_editable = ['description', 'in_use', 'update_priority']
    search_fields = ['name', 'description', 'in_use', 'update_priority']

    class Meta:
        model = Mtables


class KalaAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'name', 'code','kala_taf', 'grpcode','category', 's_m_ratio', 'total_sale']
    list_filter = ['category']
    list_editable = ['category']
    search_fields = ['name', 'code']

    class Meta:
        model = Kala


class FactorAdmin(admin.ModelAdmin):
    list_display = ['acc_year','pdate', 'code', 'create_time', 'per_code', 'person','date','mablagh_factor', 'takhfif', 'darsad_takhfif']

    list_filter = ['acc_year']
    # list_editable = ['description', 'in_use']
    # search_fields = ['name', 'code']

    class Meta:
        model = Factor


class FactorDetaileAdmin(admin.ModelAdmin):
    list_display = ['acc_year','code_factor', 'kala', 'count', 'mablagh_vahed', 'mablagh_nahaee']
    list_filter = ['acc_year']

    # list_filter = ['name','code']
    # list_editable = ['description', 'in_use']
    # search_fields = ['name', 'code']

    class Meta:
        model = FactorDetaile


class WordCountAdmin(admin.ModelAdmin):
    list_display = ['word', 'count']
    # list_filter = ['name','code']
    # list_editable = ['description', 'in_use']
    search_fields = ['word']

    class Meta:
        model = WordCount


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'name', 'parent', 'level','code_mahak']
    list_filter = ['level', 'parent', ]
    list_editable = ['name', 'parent', 'level']
    search_fields = ['name', 'level']

    class Meta:
        model = Category


class KardexAdmin(admin.ModelAdmin):
    list_display = ['acc_year','__str__', 'date', 'stock', 'code_kala', 'kala', 'count', 'ktype', 'percode', 'storage',
                    'warehousecode', 'averageprice', 'sync_mojodi']
    list_filter = ['acc_year','warehousecode', 'sync_mojodi']
    list_editable = ['sync_mojodi']
    search_fields = ['count', 'code_kala', 'stock']

    class Meta:
        model = Kardex


class MojodiAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'stock', 'total_stock', 'code_kala', 'kala', 'storage', 'warehousecode', 'averageprice',
                    'mojodi_roz', 'mojodi_roz_arzesh']
    list_filter = ['warehousecode']
    # list_editable = ['name','parent','level']
    search_fields = ['code_kala', 'stock']

    class Meta:
        model = Mojodi


class PersonAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'code','per_taf', 'name', 'lname','clname', 'group']
    # list_filter = ['level','parent',]
    list_editable = ['clname']
    search_fields = ['name', 'code','per_taf']

    class Meta:
        model = Person


class KalaGroupinfoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'id', 'code','code_mahak', 'contain', 'cat3', 'cat2', 'cat1']

    # list_filter = ['level','parent',]
    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = KalaGroupinfo


class StoragekAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'code']

    # list_filter = ['level','parent',]
    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = Storagek


class SanadAdmin(admin.ModelAdmin):
    list_display = ['acc_year','__str__', 'code', 'tarikh', 'sharh']

    list_filter = ['acc_year']
    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = Sanad


class SanadDetailAdmin(admin.ModelAdmin):
    list_display = ['acc_year','__str__', 'code', 'tarikh', 'date', 'kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes', 'curramount',
                    'is_active', 'is_analiz', 'cheque_id', 'syscomment','person']
    list_filter = ['acc_year','is_active', 'kol', 'moin', 'tafzili']
    list_editable = ['is_analiz']
    search_fields = ['tarikh', 'date', 'kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes', 'curramount', 'cheque_id']

    class Meta:
        model = SanadDetail


class AccCodingAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'code', 'name', 'level', 'parent']
    list_filter = ['level']

    # list_editable = ['name','parent','level']
    # search_fields = ['name','lname','group']

    class Meta:
        model = AccCoding


class ChequesRecieveAdmin(admin.ModelAdmin):
    list_display = (
    'id_mahak', 'cheque_id', 'cheque_row', 'issuance_tarik', 'issuance_date', 'cheque_tarik', 'cheque_date', 'cost',
    'total_mandeh', 'last_sanad_detaile', 'bank_name','bank_logo', 'bank_branch', 'account_id', 'description', 'status', 'per_code')
    # list_display = ('id_mahak' , 'cheque_row', 'issuance_tarik', 'issuance_date', 'cheque_tarik', 'cheque_date', 'cost', 'bank_name', 'bank_branch', 'account_id', 'description', 'status', 'per_code')
    search_fields = ('cheque_id', 'bank_name', 'status')
    list_filter=['bank_name']
    class Meta:
        model = ChequesRecieve


@admin.register(MyCondition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ('__str__','acc_year','kol', 'moin', 'tafzili', 'contain', 'equal_to', 'is_active', 'is_new')
    list_filter = ('is_active','acc_year',)  # امکان فیلتر کردن بر اساس وضعیت فعال بودن
    search_fields = ('kol', 'moin', 'tafzili')
    list_editable = ['kol', 'moin', 'tafzili', 'contain', 'equal_to', 'is_active','acc_year']


from django.contrib import admin
from .models import ChequesRecieve


@admin.register(ChequesPay)
class ChequesPayAdmin(admin.ModelAdmin):
    list_display = (
        'id_mahak', 'cheque_id', 'cheque_row', 'issuance_tarik', 'issuance_date',
        'cheque_tarik', 'cheque_date', 'cost', 'bank_code', 'bank', 'description',
        'status', 'firstperiod', 'cheque_id_counter', 'per_code',
        'recieve_status', 'total_mandeh', 'last_sanad_detaile'
    )
    list_filter = ('status', 'firstperiod', 'recieve_status', 'cheque_date')
    search_fields = ('cheque_id', 'per_code', 'description')
    list_per_page = 100


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = (
        'code','bank_name', 'name','bank_logo', 'shobe', 'sh_h', 'type_h', 'mogodi', 'firstamount'
    )
    list_filter = ('bank_name',)
    list_editable = ['bank_logo']
    # search_fields = ('cheque_id', 'per_code', 'description')
    list_per_page = 100



@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('code', 'person','tarikh', 'date', 'number', 'cost','loan_mandeh','actual_loan_mandeh','tasfiiye')
    search_fields = ('code', 'person__name')
    list_filter = ('person',)

@admin.register(LoanDetil)
class LoanDetilAdmin(admin.ModelAdmin):
    list_display = ('code','loan','loan_code', 'tarikh','recive_tarikh', 'date', 'cost','complete_percent')
    search_fields = ('code','loan_code', 'tarikh', 'date', 'cost')
    # list_filter = ('person',)



@admin.register(BedehiMoshtari)
class BedehiMoshtariAdmin(admin.ModelAdmin):
    list_display = ('moin','tafzili','person', 'total_mandeh','loans_total', 'total_with_loans','from_last_daryaft')
    search_fields = ('tafzili',)
    # list_filter = ('person',)




admin.site.register(Mtables, MtablesAdmin)
admin.site.register(Kala, KalaAdmin)
admin.site.register(Factor, FactorAdmin)
admin.site.register(FactorDetaile, FactorDetaileAdmin)
admin.site.register(WordCount, WordCountAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Kardex, KardexAdmin)
admin.site.register(Mojodi, MojodiAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(KalaGroupinfo, KalaGroupinfoAdmin)
admin.site.register(Storagek, StoragekAdmin)
admin.site.register(Sanad, SanadAdmin)
admin.site.register(SanadDetail, SanadDetailAdmin)
admin.site.register(AccCoding, AccCodingAdmin)
admin.site.register(ChequesRecieve, ChequesRecieveAdmin)
