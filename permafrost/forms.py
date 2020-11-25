# Permafrost Forms
from django.forms import ModelForm, MultipleChoiceField, CheckboxSelectMultiple
from django.forms.fields import CharField, ChoiceField
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _
from .models import PermafrostRole, get_optional_by_category, get_required_by_category, get_choices

CHOICES = [('', _("Choose Role Type"))] + get_choices()

def assemble_options(permissions):
    choices = []
    optgroups = {}
    if permissions:
        for perm in permissions:
            if perm.content_type.model in optgroups:
                optgroups[perm.content_type.app_label].append((perm.pk, perm.name,))
            else:
                optgroups[perm.content_type.app_label] = [(perm.pk, perm.name,)]

    for model_name, options in optgroups.items():
        choices.append([model_name, options])
    
    return choices

class SelectPermafostRoleTypeForm(ModelForm):
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attrs = self.fields['description'].widget.attrs
        
        # add Textarea w/o overwriting attrs
        self.fields['description'].widget = Textarea(attrs=attrs)
        self.fields['category'].choices = CHOICES
        category = self.initial.get('category', None)
        
        if category:  
              
            required_perms = get_required_by_category(category)
            optional_perms = get_optional_by_category(category)
            required_choices = assemble_options(required_perms)
            optional_choices = assemble_options(optional_perms)
            
            initial = [perm.pk for perm in required_perms]
            
            self.fields[f'required_{category}_perms'] = MultipleChoiceField(label=_("Required Permissions"), initial=initial, choices=required_choices, widget=CheckboxSelectMultiple(attrs={'readonly':True, 'disabled': True}))
            self.fields[f'optional_{category}_perms'] = MultipleChoiceField(label=_("Optional Permissions"), choices=optional_choices, widget=CheckboxSelectMultiple())

# class PermafrostRoleEditForm(ModelForm):
#     class Meta:
#         model = PermafrostRole
#         fields = ('name', 'description',)
#         read_only= ('category',)