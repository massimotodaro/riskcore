drop extension if exists "pg_net";

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE TRIGGER on_auth_user_deleted AFTER DELETE ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_user_deleted();

CREATE TRIGGER on_auth_user_updated AFTER UPDATE ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_user_updated();


