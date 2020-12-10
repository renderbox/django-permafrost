# Permafrost Forms
from django.contrib.auth.models import Permission
from django.forms import ModelForm, MultipleChoiceField, CheckboxSelectMultiple
from django.forms.fields import CharField, ChoiceField, BooleanField
from django.forms.widgets import CheckboxInput, Textarea
from django.utils.translation import ugettext_lazy as _
from .models import PermafrostRole, get_optional_by_category, get_required_by_category, get_choices

CHOICES = [('', _("Choose Role Type"))] + get_choices()

def assemble_optiongroups_for_widget(permissions):
    choices = []
    optgroups = {}
    if permissions:
        for perm in permissions:
            if perm.content_type.model in optgroups:
                optgroups[perm.content_type.model].append((perm.pk, perm.name,))
            else:
                optgroups[perm.content_type.model] = [(perm.pk, perm.name,)]

    for model_name, options in optgroups.items():
        choices.append([model_name, options])
    
    return choices

class SelectPermafrostRoleTypeForm(ModelForm):
    name = CharField(required=False)
    description = CharField(required=False, widget=Textarea())
    category = ChoiceField(choices=CHOICES)
    
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)


class PermafrostRoleCreateForm(ModelForm):
    class Meta:
        model = PermafrostRole
        fields = ('name', 'description', 'category',)
        widgets = {
            'description': Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].choices = CHOICES
        category = self.initial.get('category', None)
        
        for field in self.fields:
            widget = self.fields[field].widget
            if not isinstance(widget, CheckboxInput):
                if 'class' in widget.attrs:
                    widget.attrs['class'] =  widget.attrs['class'] + " form-control"
                else:
                    widget.attrs.update({'class':'form-control'})
        
        if category:  
              
            required_perms = get_required_by_category(category)
            optional_perms = get_optional_by_category(category)
            required_choices = assemble_optiongroups_for_widget(required_perms)
            optional_choices = assemble_optiongroups_for_widget(optional_perms)
            
            initial = [perm.pk for perm in required_perms]
            
            self.fields[f'required_{category}_perms'] = MultipleChoiceField(label=_("Required Permissions"), initial=initial, choices=required_choices, widget=CheckboxSelectMultiple(attrs={'readonly':True, 'disabled': True}), required=False)
            self.fields[f'optional_{category}_perms'] = MultipleChoiceField(label=_("Optional Permissions"), choices=optional_choices, widget=CheckboxSelectMultiple(), required=False)

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

class PermafrostRoleUpdateForm(PermafrostRoleCreateForm):
    """
     Form used to display role detail
     Only allowed to edit optional permissions, name and description
     Category and required permissions stay locked
    """
    category = ChoiceField(choices=CHOICES, required=False)
    deleted = BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].widget.attrs.update({'readonly': True, 'disabled': True})
        self.fields['category'].disabled = True
        self.fields['category'].required = False
        self.fields['category'].initial = self.instance.category
        
        self.fields['deleted'].initial = self.instance.deleted
        
        print(self.fields['deleted'].widget.input_type)
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
        