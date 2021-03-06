from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView

from ads.forms import CreateForm, CommentForm
from ads.models import Ad, Comment, Fav
from ads.owner import OwnerListView, OwnerDetailView, OwnerDeleteView
from django.db.models import Q
from django.contrib.humanize.templatetags.humanize import naturaltime

class AdListView(OwnerListView): # edited during adding the "fav adds section"
    template_name = "ads/ad_list.html"
    
    def get(self, request):

        strval = request.GET.get("search", False)
        # print(strval)
        if strval:
            query = Q(title__icontains = strval)
            query.add(Q(text__icontains = strval), Q.OR)
            query.add(Q(tags__name__in = [strval]), Q.OR)
            
            ad_list = Ad.objects.filter(query).select_related().distinct().order_by('-updated_at')[:10]
            # print(ad_list)
        else:
            ad_list = Ad.objects.all().order_by('-updated_at')[:10]

        for obj in ad_list:
            obj.natural_updated = naturaltime(obj.updated_at)


        favorites = list()
        
        if request.user.is_authenticated:
            rows = request.user.favorite_ads.values('id') # ids for all favorite_ads to this request_user
            # print(rows)
            favorites = [row['id'] for row in rows]
            # print(favorites)

        return render(request, self.template_name, {
            "ad_list" : ad_list,
            "favorites" : favorites,
            "search" : strval,
        })
        

class AdDetailView(OwnerDetailView):
    model = Ad
    template_name = "ads/ad_detail.html"

    def get(self, request, pk) :
        x = Ad.objects.get(id=pk)
        comments = Comment.objects.filter(ad=x).order_by('-updated_at')
        comment_form = CommentForm()
        context = { 'ad' : x, 'comments': comments, 'comment_form': comment_form }
        return render(request, self.template_name, context)



class AdCreateView(LoginRequiredMixin, CreateView):
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk=None):
        form = CreateForm()
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        form = CreateForm(request.POST, request.FILES or None)
        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)
        # Add owner to the model before saving
        ad = form.save(commit=False)
        ad.owner = self.request.user
        ad.save()

        # https://django-taggit.readthedocs.io/en/latest/forms.html#commit-false
        form.save_m2m()
        
        return redirect(self.success_url)



class AdUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(instance=ad)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(request.POST, request.FILES or None, instance=ad)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        ad = form.save(commit=False)
        ad.save()

        return redirect(self.success_url)


class AdDeleteView(OwnerDeleteView):
    model = Ad



def stream_file(request, pk):
    ad = get_object_or_404(Ad, id=pk)
    response = HttpResponse()
    response['Content-Type'] = ad.content_type
    response['Content-Length'] = len(ad.picture)
    response.write(ad.picture)
    return response



class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        f = get_object_or_404(Ad, id=pk)
        comment = Comment(text=request.POST['comment'], owner=request.user, ad=f)
        comment.save()
        return redirect(reverse('ads:ad_detail', args=[pk]))
        
        

class CommentDeleteView(OwnerDeleteView):
    model = Comment
    template_name = "ads/comment_delete.html"

    # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
    def get_success_url(self):
        ad = self.object.ad
        return reverse('ads:ad_detail', args=[ad.id])



from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError


# class AddFavoriteView(OwnerAdFavoriteView):
#     def post(self, request, pk):
#         t = get_object_or_404(Ad, id=pk)
#         fav = Fav(user=request.user, ad = t)

#         try: fav.save() # in case duplicate key
#         except IntegrityError as e: pass
#         return HttpResponse()
@method_decorator(csrf_exempt, name='dispatch')
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(pk)
        t = get_object_or_404(Ad, id=pk)
        fav = Fav(user = request.user, ad = t)

        try: fav.save() # in case duplicate key
        except IntegrityError as e: pass
        return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class DeleteFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        t = get_object_or_404(Ad, id = pk)
        try:
            fav = Fav.objects.get(user = request.user, ad = t).delete()
        except Fav.DoesNotExist as e: pass

        return HttpResponse()