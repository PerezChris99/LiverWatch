/**
 * LiverWatch - Forum Module
 * =========================
 * 
 * Forum functionality: posts, comments, voting, etc.
 */

(function() {
    'use strict';

    const { $, $$, api, formatRelativeTime, Toast, Modal, debounce } = LiverWatch;

    // =========================================
    // Post Management
    // =========================================

    const Posts = {
        currentPage: 1,
        isLoading: false,
        hasMore: true,
        category: 'all',

        init() {
            this.bindEvents();
            this.initInfiniteScroll();
        },

        bindEvents() {
            // Category filter
            $$('.category-filter').forEach(btn => {
                btn.addEventListener('click', () => {
                    $$('.category-filter').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.category = btn.dataset.category;
                    this.resetAndLoad();
                });
            });

            // Sort options
            const sortSelect = $('#post-sort');
            if (sortSelect) {
                sortSelect.addEventListener('change', () => {
                    this.resetAndLoad();
                });
            }

            // Search
            const searchInput = $('#post-search');
            if (searchInput) {
                searchInput.addEventListener('input', debounce(() => {
                    this.resetAndLoad();
                }, 300));
            }
        },

        initInfiniteScroll() {
            const sentinel = $('#posts-sentinel');
            if (!sentinel) return;

            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting && !this.isLoading && this.hasMore) {
                    this.loadMore();
                }
            }, { rootMargin: '100px' });

            observer.observe(sentinel);
        },

        async resetAndLoad() {
            this.currentPage = 1;
            this.hasMore = true;
            
            const container = $('#posts-container');
            if (container) {
                container.innerHTML = '';
            }
            
            await this.loadMore();
        },

        async loadMore() {
            if (this.isLoading || !this.hasMore) return;

            this.isLoading = true;
            this.showLoader();

            try {
                const searchInput = $('#post-search');
                const sortSelect = $('#post-sort');
                
                const params = new URLSearchParams({
                    page: this.currentPage,
                    category: this.category,
                    search: searchInput?.value || '',
                    sort: sortSelect?.value || 'recent'
                });

                const response = await api(`/forum/posts?${params}`);
                
                this.renderPosts(response.posts);
                this.hasMore = response.hasMore;
                this.currentPage++;

            } catch (error) {
                Toast.error('Failed to load posts');
                console.error('Load posts error:', error);
            } finally {
                this.isLoading = false;
                this.hideLoader();
            }
        },

        renderPosts(posts) {
            const container = $('#posts-container');
            if (!container) return;

            posts.forEach(post => {
                const postEl = this.createPostElement(post);
                container.appendChild(postEl);
            });
        },

        createPostElement(post) {
            const div = document.createElement('div');
            div.className = 'post-card animate-fade-in';
            div.dataset.postId = post.id;

            div.innerHTML = `
                <div class="post-votes">
                    <button class="vote-btn vote-up ${post.userVote === 1 ? 'upvoted' : ''}" 
                            data-vote="up" data-id="${post.id}">
                        <i class="fas fa-chevron-up"></i>
                    </button>
                    <span class="vote-count">${post.votes || 0}</span>
                    <button class="vote-btn vote-down ${post.userVote === -1 ? 'downvoted' : ''}" 
                            data-vote="down" data-id="${post.id}">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <div class="post-content">
                    <span class="post-category">
                        <i class="fas fa-tag"></i> ${post.category || 'General'}
                    </span>
                    <h3 class="post-title">
                        <a href="/forum/post/${post.id}">${this.escapeHtml(post.title)}</a>
                    </h3>
                    <p class="post-excerpt">${this.escapeHtml(post.excerpt || '')}</p>
                    <div class="post-meta">
                        <span class="post-author">
                            <img src="${post.author?.avatar || '/static/images/default-avatar.png'}" 
                                 alt="${post.author?.username || 'Anonymous'}">
                            ${post.author?.username || 'Anonymous'}
                        </span>
                        <span class="post-stat">
                            <i class="fas fa-clock"></i> ${formatRelativeTime(post.created_at)}
                        </span>
                        <span class="post-stat">
                            <i class="fas fa-comment"></i> ${post.comments_count || 0}
                        </span>
                        <span class="post-stat">
                            <i class="fas fa-eye"></i> ${post.views || 0}
                        </span>
                    </div>
                </div>
            `;

            return div;
        },

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        showLoader() {
            const sentinel = $('#posts-sentinel');
            if (sentinel) {
                sentinel.innerHTML = '<div class="spinner mx-auto"></div>';
            }
        },

        hideLoader() {
            const sentinel = $('#posts-sentinel');
            if (sentinel) {
                sentinel.innerHTML = this.hasMore 
                    ? '' 
                    : '<p class="text-center text-muted">No more posts</p>';
            }
        }
    };

    // =========================================
    // Voting System
    // =========================================

    const Voting = {
        init() {
            document.addEventListener('click', (e) => {
                const voteBtn = e.target.closest('.vote-btn');
                if (voteBtn) {
                    this.handleVote(voteBtn);
                }
            });
        },

        async handleVote(button) {
            const postId = button.dataset.id;
            const direction = button.dataset.vote;
            const container = button.closest('.post-votes') || button.closest('.comment-votes');
            const countEl = $('.vote-count', container);

            // Check if user is logged in
            if (!window.currentUser) {
                Toast.warning('Please log in to vote');
                return;
            }

            // Optimistic update
            const currentCount = parseInt(countEl.textContent) || 0;
            const upBtn = $('.vote-up', container);
            const downBtn = $('.vote-down', container);
            const wasUpvoted = upBtn.classList.contains('upvoted');
            const wasDownvoted = downBtn.classList.contains('downvoted');

            let newCount = currentCount;

            // Calculate new count
            if (direction === 'up') {
                if (wasUpvoted) {
                    newCount -= 1;
                    upBtn.classList.remove('upvoted');
                } else {
                    newCount += wasDownvoted ? 2 : 1;
                    upBtn.classList.add('upvoted');
                    downBtn.classList.remove('downvoted');
                }
            } else {
                if (wasDownvoted) {
                    newCount += 1;
                    downBtn.classList.remove('downvoted');
                } else {
                    newCount -= wasUpvoted ? 2 : 1;
                    downBtn.classList.add('downvoted');
                    upBtn.classList.remove('upvoted');
                }
            }

            // Animate count update
            countEl.classList.add('counting');
            countEl.textContent = newCount;
            setTimeout(() => countEl.classList.remove('counting'), 300);

            try {
                const response = await api(`/forum/vote`, {
                    method: 'POST',
                    body: { postId, direction }
                });

                // Sync with server count
                if (response.count !== undefined) {
                    countEl.textContent = response.count;
                }
            } catch (error) {
                // Revert on error
                countEl.textContent = currentCount;
                if (wasUpvoted) upBtn.classList.add('upvoted');
                else upBtn.classList.remove('upvoted');
                if (wasDownvoted) downBtn.classList.add('downvoted');
                else downBtn.classList.remove('downvoted');

                Toast.error('Failed to register vote');
            }
        }
    };

    // =========================================
    // Comments System
    // =========================================

    const Comments = {
        postId: null,

        init() {
            this.postId = $('#comments-section')?.dataset.postId;
            if (!this.postId) return;

            this.bindEvents();
        },

        bindEvents() {
            // Submit comment
            const form = $('#comment-form');
            if (form) {
                form.addEventListener('submit', (e) => this.handleSubmit(e));
            }

            // Reply buttons
            document.addEventListener('click', (e) => {
                const replyBtn = e.target.closest('.reply-btn');
                if (replyBtn) {
                    this.showReplyForm(replyBtn);
                }
            });

            // Delete comment
            document.addEventListener('click', (e) => {
                const deleteBtn = e.target.closest('.delete-comment');
                if (deleteBtn) {
                    this.confirmDelete(deleteBtn.dataset.commentId);
                }
            });

            // Edit comment
            document.addEventListener('click', (e) => {
                const editBtn = e.target.closest('.edit-comment');
                if (editBtn) {
                    this.showEditForm(editBtn.dataset.commentId);
                }
            });
        },

        async handleSubmit(e) {
            e.preventDefault();

            const form = e.target;
            const content = form.querySelector('[name="content"]').value.trim();
            const parentId = form.dataset.parentId || null;

            if (!content) {
                Toast.warning('Please enter a comment');
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner spinner-sm"></span>';

            try {
                const response = await api(`/forum/comment`, {
                    method: 'POST',
                    body: {
                        postId: this.postId,
                        content,
                        parentId
                    }
                });

                // Add comment to DOM
                this.addCommentToDOM(response.comment, parentId);

                // Reset form
                form.reset();
                if (parentId) {
                    form.remove();
                }

                // Update count
                this.updateCommentCount(1);

                Toast.success('Comment posted!');

            } catch (error) {
                Toast.error('Failed to post comment');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Post Comment';
            }
        },

        addCommentToDOM(comment, parentId) {
            const html = this.createCommentHTML(comment);
            
            if (parentId) {
                const parentComment = $(`[data-comment-id="${parentId}"]`);
                let repliesContainer = $('.comment-replies', parentComment);
                
                if (!repliesContainer) {
                    repliesContainer = document.createElement('div');
                    repliesContainer.className = 'comment-replies';
                    parentComment.appendChild(repliesContainer);
                }
                
                repliesContainer.insertAdjacentHTML('beforeend', html);
            } else {
                const container = $('#comments-list');
                container.insertAdjacentHTML('afterbegin', html);
            }

            // Animate new comment
            const newComment = $(`[data-comment-id="${comment.id}"]`);
            newComment.classList.add('animate-fade-in');
        },

        createCommentHTML(comment) {
            return `
                <div class="comment ${comment.parentId ? 'comment-reply' : ''}" 
                     data-comment-id="${comment.id}">
                    <img src="${comment.author?.avatar || '/static/images/default-avatar.png'}" 
                         alt="${comment.author?.username}" 
                         class="comment-avatar">
                    <div class="comment-content">
                        <div class="comment-header">
                            <span class="comment-author">${comment.author?.username || 'Anonymous'}</span>
                            <span class="comment-date">${formatRelativeTime(comment.created_at)}</span>
                        </div>
                        <div class="comment-body">
                            ${this.escapeHtml(comment.content)}
                        </div>
                        <div class="comment-actions">
                            <button class="comment-action reply-btn" data-comment-id="${comment.id}">
                                <i class="fas fa-reply"></i> Reply
                            </button>
                            ${comment.canEdit ? `
                                <button class="comment-action edit-comment" data-comment-id="${comment.id}">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                                <button class="comment-action delete-comment" data-comment-id="${comment.id}">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        },

        showReplyForm(button) {
            const commentId = button.dataset.commentId;
            const comment = button.closest('.comment');
            
            // Remove any existing reply forms
            $$('.reply-form').forEach(f => f.remove());

            const form = document.createElement('form');
            form.className = 'reply-form comment-form mt-3 animate-fade-in';
            form.dataset.parentId = commentId;
            form.innerHTML = `
                <textarea name="content" class="form-control" 
                          placeholder="Write a reply..." rows="3" required></textarea>
                <div class="d-flex justify-between mt-2">
                    <button type="button" class="btn btn-secondary cancel-reply">Cancel</button>
                    <button type="submit" class="btn btn-primary">Reply</button>
                </div>
            `;

            comment.appendChild(form);
            form.querySelector('textarea').focus();

            // Cancel button
            form.querySelector('.cancel-reply').addEventListener('click', () => {
                form.remove();
            });

            // Submit handler
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        },

        showEditForm(commentId) {
            const comment = $(`[data-comment-id="${commentId}"]`);
            const body = $('.comment-body', comment);
            const originalContent = body.textContent;

            body.innerHTML = `
                <form class="edit-form">
                    <textarea class="form-control" rows="3">${originalContent}</textarea>
                    <div class="d-flex justify-between mt-2">
                        <button type="button" class="btn btn-secondary cancel-edit">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save</button>
                    </div>
                </form>
            `;

            const form = $('.edit-form', body);
            form.querySelector('textarea').focus();

            form.querySelector('.cancel-edit').addEventListener('click', () => {
                body.textContent = originalContent;
            });

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const newContent = form.querySelector('textarea').value.trim();

                if (!newContent) return;

                try {
                    await api(`/forum/comment/${commentId}`, {
                        method: 'PUT',
                        body: { content: newContent }
                    });

                    body.textContent = newContent;
                    Toast.success('Comment updated');
                } catch (error) {
                    Toast.error('Failed to update comment');
                    body.textContent = originalContent;
                }
            });
        },

        confirmDelete(commentId) {
            Modal.confirm(
                'Are you sure you want to delete this comment?',
                async () => {
                    try {
                        await api(`/forum/comment/${commentId}`, {
                            method: 'DELETE'
                        });

                        const comment = $(`[data-comment-id="${commentId}"]`);
                        comment.style.animation = 'fadeOut 0.3s ease forwards';
                        setTimeout(() => comment.remove(), 300);

                        this.updateCommentCount(-1);
                        Toast.success('Comment deleted');
                    } catch (error) {
                        Toast.error('Failed to delete comment');
                    }
                }
            );
        },

        updateCommentCount(delta) {
            const countEl = $('.comments-title .badge');
            if (countEl) {
                const current = parseInt(countEl.textContent) || 0;
                countEl.textContent = Math.max(0, current + delta);
            }
        },

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // =========================================
    // Post Editor
    // =========================================

    const PostEditor = {
        form: null,
        contentEditor: null,

        init() {
            this.form = $('#post-form');
            if (!this.form) return;

            this.initTextarea();
            this.bindEvents();
        },

        initTextarea() {
            const textarea = $('#post-content', this.form);
            if (!textarea) return;

            // Auto-resize
            textarea.addEventListener('input', () => {
                textarea.style.height = 'auto';
                textarea.style.height = `${textarea.scrollHeight}px`;
            });

            // Markdown shortcuts
            textarea.addEventListener('keydown', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    switch (e.key) {
                        case 'b':
                            e.preventDefault();
                            this.wrapSelection('**', '**');
                            break;
                        case 'i':
                            e.preventDefault();
                            this.wrapSelection('*', '*');
                            break;
                        case 'k':
                            e.preventDefault();
                            this.wrapSelection('[', '](url)');
                            break;
                    }
                }
            });
        },

        wrapSelection(before, after) {
            const textarea = $('#post-content', this.form);
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const text = textarea.value;
            const selected = text.substring(start, end);

            textarea.value = text.substring(0, start) + before + selected + after + text.substring(end);
            textarea.focus();
            textarea.selectionStart = start + before.length;
            textarea.selectionEnd = start + before.length + selected.length;
        },

        bindEvents() {
            // Preview toggle
            const previewBtn = $('#toggle-preview');
            if (previewBtn) {
                previewBtn.addEventListener('click', () => this.togglePreview());
            }

            // Form submission
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));

            // Auto-save draft
            const titleInput = $('#post-title', this.form);
            const contentInput = $('#post-content', this.form);

            [titleInput, contentInput].forEach(input => {
                if (input) {
                    input.addEventListener('input', debounce(() => this.saveDraft(), 1000));
                }
            });

            // Load existing draft
            this.loadDraft();
        },

        togglePreview() {
            const content = $('#post-content', this.form);
            const preview = $('#post-preview');
            
            if (!preview) return;

            if (preview.classList.contains('hidden')) {
                // Show preview
                preview.innerHTML = this.renderMarkdown(content.value);
                preview.classList.remove('hidden');
                content.classList.add('hidden');
            } else {
                // Show editor
                preview.classList.add('hidden');
                content.classList.remove('hidden');
            }
        },

        renderMarkdown(text) {
            // Basic markdown rendering
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
                .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                .replace(/\n/g, '<br>');
        },

        saveDraft() {
            const titleInput = $('#post-title', this.form);
            const contentInput = $('#post-content', this.form);
            const categorySelect = $('#post-category', this.form);

            const draft = {
                title: titleInput?.value || '',
                content: contentInput?.value || '',
                category: categorySelect?.value || '',
                savedAt: new Date().toISOString()
            };

            LiverWatch.storage.set('post-draft', draft);
        },

        loadDraft() {
            const draft = LiverWatch.storage.get('post-draft');
            if (!draft) return;

            // Don't load draft if editing existing post
            if (this.form.dataset.editId) return;

            const titleInput = $('#post-title', this.form);
            const contentInput = $('#post-content', this.form);
            const categorySelect = $('#post-category', this.form);

            if (draft.title && titleInput) titleInput.value = draft.title;
            if (draft.content && contentInput) contentInput.value = draft.content;
            if (draft.category && categorySelect) categorySelect.value = draft.category;

            // Show notification
            if (draft.title || draft.content) {
                Toast.info('Draft restored');
            }
        },

        clearDraft() {
            LiverWatch.storage.remove('post-draft');
        },

        async handleSubmit(e) {
            e.preventDefault();

            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData);

            const submitBtn = this.form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner spinner-sm"></span> Posting...';

            try {
                const endpoint = this.form.dataset.editId 
                    ? `/forum/post/${this.form.dataset.editId}`
                    : '/forum/post';
                
                const method = this.form.dataset.editId ? 'PUT' : 'POST';

                const response = await api(endpoint, { method, body: data });

                this.clearDraft();
                Toast.success(this.form.dataset.editId ? 'Post updated!' : 'Post created!');
                
                // Redirect to post
                setTimeout(() => {
                    window.location.href = `/forum/post/${response.post.id}`;
                }, 500);

            } catch (error) {
                Toast.error('Failed to save post');
                submitBtn.disabled = false;
                submitBtn.innerHTML = this.form.dataset.editId ? 'Update Post' : 'Create Post';
            }
        }
    };

    // =========================================
    // Initialize
    // =========================================

    function init() {
        Posts.init();
        Voting.init();
        Comments.init();
        PostEditor.init();
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // =========================================
    // Export
    // =========================================

    LiverWatch.Forum = {
        Posts,
        Voting,
        Comments,
        PostEditor
    };

})();
