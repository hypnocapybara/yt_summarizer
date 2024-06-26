#
# SPEAKERS = [
#     'Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema', 'Alison Dietlinde', 'Ana Florence',
#     'Annmarie Nele', 'Asya Anara', 'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen',
#     'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper', 'Badr Odhiambo', 'Dionisio Schuyler',
#     'Royston Min', 'Viktor Eka', 'Abrahan Mack', 'Adde Michal', 'Baldur Sanjin', 'Craig Gutsy', 'Damien Black',
#     'Gilberto Mathias', 'Ilkin Urbano', 'Kazuhiko Atallah', 'Ludvig Milivoj', 'Suad Qasim', 'Torcull Diarmuid',
#     'Viktor Menelaos', 'Zacharie Aimilios', 'Nova Hogarth', 'Maja Ruoho', 'Uta Obando', 'Lidiya Szekeres',
#     'Chandra MacFarland', 'Szofi Granger', 'Camilla Holmström', 'Lilya Stainthorpe', 'Zofija Kendrick',
#     'Narelle Moon', 'Barbora MacLean', 'Alexandra Hisakawa', 'Alma María', 'Rosemary Okafor', 'Ige Behringer',
#     'Filip Traverse', 'Damjan Chapman', 'Wulf Carlevaro', 'Aaron Dreschner', 'Kumar Dahl', 'Eugenio Mataracı',
#     'Ferran Simen', 'Xavier Hayasaka', 'Luis Moray', 'Marcos Rudaski'
# ]
#
#
# def voice_summary_tts(video: YoutubeVideo):
#     if not video.summary:
#         return
#
#     device = 'cuda' if torch.cuda.is_available() else 'cpu'
#     tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to(device)
#     _fd, temp_filename = tempfile.mkstemp()
#     try:
#         if video.channel and video.channel.voice_file:
#             speaker_params = {'speaker_wav': video.channel.voice_file.path}
#         else:
#             speaker_params = {'speaker': random.choice(SPEAKERS)}
#
#         tts.tts_to_file(
#             text=video.summary,
#             language=video.transcription_language,
#             file_path=temp_filename,
#             **speaker_params,
#         )
#         with open(temp_filename, 'rb') as file:
#             video.voiced_summary.save(f'{video.youtube_id}.wav', file)
#             video.save()
#     finally:
#         os.remove(temp_filename)
