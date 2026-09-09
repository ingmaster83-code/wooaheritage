require 'json'

module Jekyll
  class MuseumPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      items = load_json(site, '_rawdata/museum.json')

      Jekyll.logger.info "MuseumGenerator:", "#{items.size}개 박물관·미술관 페이지 생성 중..."
      items.each do |m|
        next if m['slug'].to_s.strip.empty?
        site.pages << MuseumPage.new(site, m)
      end

      Jekyll.logger.info "MuseumGenerator:", "완료 (#{items.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "MuseumGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class MuseumPage < Page
    def initialize(site, m)
      @site = site
      @base = site.source
      @dir  = "museum/#{m['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'museum.html')
      self.data.merge!(m)
      self.data['layout']      = 'museum'
      self.data['title']       = build_title(m)
      self.data['description'] = build_desc(m)
    end

    private

    def build_title(m)
      loc = [m['doShort'], m['sigungu']].compact.join(' ')
      "#{m['museumName']} #{loc} 관람시간·요금 안내"
    end

    def build_desc(m)
      loc = [m['doShort'], m['sigungu']].compact.join(' ')
      intro = (m['intro'] || '').gsub(/\s+/, ' ')
      "#{loc} #{m['museumName']}(#{m['type']}). #{intro}"[0, 155]
    end
  end
end
