# Permafrost Forms
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.forms import ModelForm, MultipleChoiceField, CheckboxSelectMultiple
from django.forms.fields import CharField, ChoiceField, BooleanField
from django.forms.widgets import CheckboxInput, Textarea
from django.utils.translation import ugettext_lazy as _
from .models import PermafrostRole, get_optional_by_category, get_required_by_category, get_choices

CHOICES = [('', _("Choose Role Type"))] + get_choices()

LABELS = {
    'name': _('Role Name'),
    'category': _('Role Type')
}

def assemble_optiongroups_for_widget(permissions):
    choices = []
    optgroups = {}
    if permissions:
        for perm in permissions:
            if perm.content_type.name in optgroups:
                optgroups[perm.content_type.name].append((perm.pk, perm.name,))
            else:
                optgroups[perm.content_type.name] = [(perm.pk, perm.name,)]

    for model_name, options in optgroups.items():
        choices.append([model_name, options])
    
    return choices

def bootstrappify(fields):
    for field in fields:
        widget = fields[field].widget
        if not isinstance(widget, CheckboxInput):
            if 'class' in widget.attrs:
                widget.attrs['class'] =  widget.attrs['class'] + " form-control"
            else:
                widget.attrs.update({'class':'form-control'})

class SelectPermafrostRoleTypeForm(ModelForm):
    name = CharField(required=False)
    description = CharField(required=False, widget=Textarea())
    category = ChoiceField(choices=CHOICES)
    
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)
        labels = LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bootstrappify(self.fields)

    


class PermafrostRoleCreateForm(ModelForm):
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)
        widgets = {
            'description': Textarea(),
        }
        labels = LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].choices = CHOICES
        category = self.initial.get(
            'category', 
            self.data.get('category', None)
        )
        
        bootstrappify(self.fields)
        
        if category:  

            required_perms = get_required_by_category(category)
            optional_perms = get_optional_by_category(category)
            required_choices = assemble_optiongroups_for_widget(required_perms)
            optional_choices = assemble_optiongroups_for_widget(optional_perms)
            
            initial = [perm.pk for perm in required_perms]
            self.fields[f'optional_{category}_perms'] = MultipleChoiceField(label=_("Optional Permissions"), choices=optional_choices, widget=CheckboxSelectMultiple(), required=False)
            self.fields[f'required_{category}_perms'] = MultipleChoiceField(label=_("Required Permissions"), initial=initial, choices=required_choices, widget=CheckboxSelectMultiple(attrs={'readonly':True, 'disabled': True}), required=False)

    def save(self, commit=True):
        instance = super().save(commit)
        category = instance.category
        if self.cleaned_data and f'optional_{category}_perms' in self.cleaned_data:
            perm_ids = []
            if category:
                perm_ids = self.cleaned_data[f'optional_{category}_perms' ]
            if perm_ids:
                instance.permissions_set(Permission.objects.filter(id__in=perm_ids))
            else:
                instance.permissions_clear()
        return instance

    def clean_name(self):
        name = self.cleaned_data['name']
        name_exists = False
       
        if self.instance:  ## on update check if name change exists

            if 'name' in self.changed_data:
                name_exists = PermafrostRole.objects.filter(

                    name=name, 
                    site__id=settings.SITE_ID,

                ).exclude(pk=self.instance.pk).first()
            
        else:

            try:
                name_exists = PermafrostRole.objects.get(
                    name=name, 
                    site__id=settings.SITE_ID
                )
            except PermafrostRole.DoesNotExist:
                pass
        
        if name_exists:
            raise ValidationError('Role with this name already exists')

        # Always return field
        return name

class PermafrostRoleUpdateForm(PermafrostRoleCreateForm):
    """
     Form used to display role detail
     Only allowed to edit optional permissions, name and description
     Category and required permissions stay locked
    """
    deleted = BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].widget.attrs.update({'readonly': True, 'disabled': True})
        self.fields['category'].disabled = True
        self.fields['category'].required = False
        self.fields['category'].initial = self.instance.category
        
        self.fields['deleted'].initial = self.instance.deleted
        
        category = self.instance.category

        optional_perms = get_optional_by_category(category)
        optional_choices = assemble_optiongroups_for_widget(optional_perms)
        
        available_optional_ids = [permission.id for permission in optional_perms]
        preselected_optional = [permission.id for permission in self.instance.permissions().all() if permission.id in available_optional_ids]

        self.fields.update({
            f'optional_{category}_perms': MultipleChoiceField(
                label=_("Optional Permissions"), 
                initial=preselected_optional, 
                choices=optional_choices, 
                widget=CheckboxSelectMultiple(),
                required=False
            )
        })

    def save(self, commit=True):
        if self.cleaned_data['deleted']:
            self.instance.deleted = self.cleaned_data['deleted']
        instance = super().save(commit)
        return instance
        