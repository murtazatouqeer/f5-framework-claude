# Django View Template

## Overview

Template for generating Django function-based and class-based views.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VIEW_NAME` | View class/function name | `ProductListView` |
| `VIEW_TYPE` | Type of view | `list`, `detail`, `create` |
| `TEMPLATE_NAME` | Template path | `products/list.html` |
| `MODEL_NAME` | Associated model | `Product` |
| `FORM_CLASS` | Form for create/update | `ProductForm` |

## Function-Based View Template

```python
# apps/{{APP_NAME}}/views/{{VIEW_NAME_SNAKE}}.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
{% if FORM_CLASS %}
from apps.{{APP_NAME}}.forms import {{FORM_CLASS}}
{% endif %}


{% if VIEW_TYPE == 'list' %}
@login_required
def {{VIEW_NAME_SNAKE}}(request):
    """List {{MODEL_NAME}} with pagination and search."""
    queryset = {{MODEL_NAME}}.objects.all()

    # Search
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    # Ordering
    ordering = request.GET.get('ordering', '-created_at')
    queryset = queryset.order_by(ordering)

    # Pagination
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    items = paginator.get_page(page)

    context = {
        'items': items,
        'search': search,
        'status': status,
    }
    return render(request, '{{TEMPLATE_NAME}}', context)
{% endif %}

{% if VIEW_TYPE == 'detail' %}
@login_required
def {{VIEW_NAME_SNAKE}}(request, pk):
    """Display {{MODEL_NAME}} detail."""
    item = get_object_or_404({{MODEL_NAME}}, pk=pk)

    context = {
        'item': item,
    }
    return render(request, '{{TEMPLATE_NAME}}', context)
{% endif %}

{% if VIEW_TYPE == 'create' %}
@login_required
def {{VIEW_NAME_SNAKE}}(request):
    """Create new {{MODEL_NAME}}."""
    if request.method == 'POST':
        form = {{FORM_CLASS}}(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            messages.success(request, '{{MODEL_NAME}} created successfully.')
            return redirect('{{APP_NAME}}:{{MODEL_NAME_SNAKE}}_detail', pk=item.pk)
    else:
        form = {{FORM_CLASS}}()

    context = {
        'form': form,
    }
    return render(request, '{{TEMPLATE_NAME}}', context)
{% endif %}

{% if VIEW_TYPE == 'update' %}
@login_required
def {{VIEW_NAME_SNAKE}}(request, pk):
    """Update {{MODEL_NAME}}."""
    item = get_object_or_404({{MODEL_NAME}}, pk=pk)

    if request.method == 'POST':
        form = {{FORM_CLASS}}(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '{{MODEL_NAME}} updated successfully.')
            return redirect('{{APP_NAME}}:{{MODEL_NAME_SNAKE}}_detail', pk=item.pk)
    else:
        form = {{FORM_CLASS}}(instance=item)

    context = {
        'form': form,
        'item': item,
    }
    return render(request, '{{TEMPLATE_NAME}}', context)
{% endif %}

{% if VIEW_TYPE == 'delete' %}
@login_required
def {{VIEW_NAME_SNAKE}}(request, pk):
    """Delete {{MODEL_NAME}}."""
    item = get_object_or_404({{MODEL_NAME}}, pk=pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, '{{MODEL_NAME}} deleted successfully.')
        return redirect('{{APP_NAME}}:{{MODEL_NAME_SNAKE}}_list')

    context = {
        'item': item,
    }
    return render(request, '{{TEMPLATE_NAME}}', context)
{% endif %}
```

## Class-Based View Template

```python
# apps/{{APP_NAME}}/views/{{VIEW_NAME_SNAKE}}.py
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
{% if FORM_CLASS %}
from apps.{{APP_NAME}}.forms import {{FORM_CLASS}}
{% endif %}


class {{MODEL_NAME}}ListView(LoginRequiredMixin, ListView):
    """List view for {{MODEL_NAME}}."""

    model = {{MODEL_NAME}}
    template_name = '{{APP_NAME}}/{{MODEL_NAME_SNAKE}}_list.html'
    context_object_name = 'items'
    paginate_by = 25
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on request parameters."""
        queryset = super().get_queryset()

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context


class {{MODEL_NAME}}DetailView(LoginRequiredMixin, DetailView):
    """Detail view for {{MODEL_NAME}}."""

    model = {{MODEL_NAME}}
    template_name = '{{APP_NAME}}/{{MODEL_NAME_SNAKE}}_detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        """Add related objects to context."""
        context = super().get_context_data(**kwargs)
        {% if RELATED_OBJECTS %}
        context['related_items'] = self.object.{{RELATED_OBJECTS}}.all()
        {% endif %}
        return context


class {{MODEL_NAME}}CreateView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    CreateView
):
    """Create view for {{MODEL_NAME}}."""

    model = {{MODEL_NAME}}
    {% if FORM_CLASS %}
    form_class = {{FORM_CLASS}}
    {% else %}
    fields = {{FIELDS}}
    {% endif %}
    template_name = '{{APP_NAME}}/{{MODEL_NAME_SNAKE}}_form.html'
    success_message = '{{MODEL_NAME}} created successfully.'

    def form_valid(self, form):
        """Set created_by to current user."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to detail view."""
        return reverse_lazy(
            '{{APP_NAME}}:{{MODEL_NAME_SNAKE}}_detail',
            kwargs={'pk': self.object.pk}
        )


class {{MODEL_NAME}}UpdateView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    UpdateView
):
    """Update view for {{MODEL_NAME}}."""

    model = {{MODEL_NAME}}
    {% if FORM_CLASS %}
    form_class = {{FORM_CLASS}}
    {% else %}
    fields = {{FIELDS}}
    {% endif %}
    template_name = '{{APP_NAME}}/{{MODEL_NAME_SNAKE}}_form.html'
    success_message = '{{MODEL_NAME}} updated successfully.'

    def get_success_url(self):
        """Redirect to detail view."""
        return reverse_lazy(
            '{{APP_NAME}}:{{MODEL_NAME_SNAKE}}_detail',
            kwargs={'pk': self.object.pk}
        )


class {{MODEL_NAME}}DeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView
):
    """Delete view for {{MODEL_NAME}}."""

    model = {{MODEL_NAME}}
    template_name = '{{APP_NAME}}/{{MODEL_NAME_SNAKE}}_confirm_delete.html'
    success_url = reverse_lazy('{{APP_NAME}}:{{MODEL_NAME_SNAKE}}_list')
    permission_required = '{{APP_NAME}}.delete_{{MODEL_NAME_SNAKE}}'

    def delete(self, request, *args, **kwargs):
        """Add success message on delete."""
        messages.success(request, '{{MODEL_NAME}} deleted successfully.')
        return super().delete(request, *args, **kwargs)
```

## URL Configuration

```python
# apps/{{APP_NAME}}/urls.py
from django.urls import path

from apps.{{APP_NAME}}.views import (
    {{MODEL_NAME}}ListView,
    {{MODEL_NAME}}DetailView,
    {{MODEL_NAME}}CreateView,
    {{MODEL_NAME}}UpdateView,
    {{MODEL_NAME}}DeleteView,
)

app_name = '{{APP_NAME}}'

urlpatterns = [
    path('', {{MODEL_NAME}}ListView.as_view(), name='{{MODEL_NAME_SNAKE}}_list'),
    path('create/', {{MODEL_NAME}}CreateView.as_view(), name='{{MODEL_NAME_SNAKE}}_create'),
    path('<uuid:pk>/', {{MODEL_NAME}}DetailView.as_view(), name='{{MODEL_NAME_SNAKE}}_detail'),
    path('<uuid:pk>/edit/', {{MODEL_NAME}}UpdateView.as_view(), name='{{MODEL_NAME_SNAKE}}_update'),
    path('<uuid:pk>/delete/', {{MODEL_NAME}}DeleteView.as_view(), name='{{MODEL_NAME_SNAKE}}_delete'),
]
```

## Mixin Patterns

### Owner Access Mixin

```python
class OwnerRequiredMixin:
    """Restrict access to object owner."""

    def get_queryset(self):
        """Filter to user's own objects."""
        return super().get_queryset().filter(
            created_by=self.request.user
        )


class {{MODEL_NAME}}UpdateView(OwnerRequiredMixin, UpdateView):
    # Only owner can update
    pass
```

### Staff Access Mixin

```python
class StaffRequiredMixin(LoginRequiredMixin):
    """Restrict access to staff users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
```

### AJAX Response Mixin

```python
from django.http import JsonResponse

class AjaxResponseMixin:
    """Return JSON for AJAX requests."""

    def form_valid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object = form.save()
            return JsonResponse({
                'success': True,
                'id': str(self.object.pk),
                'message': self.success_message
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
```

## Usage Example

```yaml
input:
  APP_NAME: products
  MODEL_NAME: Product
  MODEL_NAME_SNAKE: product
  FORM_CLASS: ProductForm
  FIELDS: "['name', 'description', 'price', 'category', 'status']"
  RELATED_OBJECTS: reviews
```

## Best Practices

1. **Use CBV for standard CRUD** - cleaner, more reusable
2. **Use FBV for complex logic** - when CBV becomes unwieldy
3. **Apply mixins consistently** - authentication, permissions
4. **Handle both GET and POST** - in form views
5. **Add success messages** - user feedback
6. **Paginate list views** - performance
7. **Filter in get_queryset** - not in template
