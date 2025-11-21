def get_user_context(user, input_title=None):
    profile = getattr(user, 'profile', None)

    if input_title:
        job_title = input_title
    elif profile and profile.current_job_title:
        job_title = profile.current_job_title
    elif profile and profile.cv_data:
        job_title = profile.cv_data.get('current_job')
    else:
        job_title = None

    skills = []
    if profile:
        if profile.skills:
            skills.extend(profile.skills)
        if profile.cv_data:
            skills.extend(profile.cv_data.get('skills', []))

    return {
        "job_title": job_title,
        "skills": list(set(skills)),
        "cv_data": profile.cv_data if profile else {}
    }